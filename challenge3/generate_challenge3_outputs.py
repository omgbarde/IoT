#!/usr/bin/env python3
import argparse
import ast
import csv
import json
import random
import re
import time
from collections import defaultdict
from pathlib import Path

TARGET_ATTR_NAMES = {
    "active power": "Active Power",
    "rms current": "RMS Current",
    "rms voltage": "RMS Voltage",
}

DATA_TYPE_CODE_TO_KEY = {
    "0x10": "Boolean",
    "0x18": "Bitmap8",
    "0x19": "Bitmap16",
    "0x1A": "Bitmap24",
    "0x1B": "Bitmap32",
    "0x20": "Uint8",
    "0x21": "Uint16",
    "0x22": "Uint24",
    "0x23": "Uint32",
    "0x24": "Uint40",
    "0x25": "Uint48",
    "0x26": "Uint56",
    "0x27": "Uint64",
    "0x28": "Int8",
    "0x29": "Int16",
    "0x2A": "Int24",
    "0x2B": "Int32",
    "0x2C": "Int40",
    "0x2D": "Int48",
    "0x2E": "Int56",
    "0x2F": "Int64",
    "0x30": "Enum8",
    "0x31": "Enum16",
}

HEX_SUFFIX_RE = re.compile(r"\s*\(0x[0-9a-fA-F]+\)\s*$")
HEX_CODE_RE = re.compile(r"\(0x[0-9a-fA-F]+\)")
LEADING_INT_RE = re.compile(r"^\s*(-?\d+)")
HEX_ONLY_RE = re.compile(r"^\s*0x([0-9a-fA-F]+)\s*$")


def listify(value):
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def parse_command_string(raw):
    if raw is None:
        return {}
    raw = raw.strip()
    if not raw:
        return {}
    try:
        return ast.literal_eval(raw)
    except Exception:
        return {}


def clean_label(value):
    if value is None:
        return ""
    text = str(value).strip()
    return HEX_SUFFIX_RE.sub("", text).strip()


def parse_hex_int(value):
    text = str(value).strip().lower()
    if re.fullmatch(r"[0-9a-f]+", text):
        try:
            return int(text, 16)
        except ValueError:
            return None
    if text.startswith("0x"):
        try:
            return int(text, 16)
        except ValueError:
            return None
    return None


def normalize_hex_addr(value):
    parsed = parse_hex_int(value)
    if parsed is not None:
        hex_digits = format(parsed, "x")
        width = max(4, len(hex_digits))
        return f"0x{parsed:0{width}x}"
    return str(value).strip().lower()


def pick_by_index(values, index):
    if not values:
        return ""
    if index < len(values):
        return values[index]
    return values[-1]


def dtype_to_value_key(dtype_value):
    if not dtype_value:
        return None
    match = HEX_CODE_RE.search(str(dtype_value))
    if not match:
        return None
    code = match.group(0)[1:-1].lower()  # strip parentheses
    return DATA_TYPE_CODE_TO_KEY.get(code)


def normalize_data_value(raw):
    if raw is None:
        return ""
    if isinstance(raw, bool):
        return "1" if raw else "0"
    if isinstance(raw, (int, float)):
        return str(int(raw))
    text = str(raw).strip()
    if not text:
        return ""
    int_match = LEADING_INT_RE.match(text)
    if int_match:
        return int_match.group(1)
    hex_match = HEX_ONLY_RE.match(text)
    if hex_match:
        return str(int(hex_match.group(1), 16))
    return text


def extract_target_attributes(cmd_obj, timestamp):
    attrs = listify(cmd_obj.get("Attribute"))
    if not attrs:
        return []

    statuses = listify(cmd_obj.get("Status"))
    data_types = listify(cmd_obj.get("Data Type"))

    value_cursors = defaultdict(int)
    extracted = []

    for idx, attr in enumerate(attrs):
        attr_name_clean = clean_label(attr)
        attr_key = attr_name_clean.lower()

        status_raw = pick_by_index(statuses, idx)
        dtype_raw = pick_by_index(data_types, idx)

        status_clean = clean_label(status_raw)
        dtype_clean = clean_label(dtype_raw)

        value_key = dtype_to_value_key(dtype_raw)
        data_value = ""

        if value_key:
            raw_values = cmd_obj.get(value_key)
            if isinstance(raw_values, list):
                cursor = value_cursors[value_key]
                if raw_values:
                    picked = raw_values[cursor] if cursor < len(raw_values) else raw_values[-1]
                    data_value = normalize_data_value(picked)
                value_cursors[value_key] = cursor + 1
            else:
                data_value = normalize_data_value(raw_values)
                value_cursors[value_key] += 1

        # Keep only rows that actually expose a typed value.
        # Read-attribute requests contain target names but no status/type/value payload.
        if attr_key in TARGET_ATTR_NAMES and dtype_clean and data_value != "":
            extracted.append(
                {
                    "Timestamp": timestamp,
                    "Sequence Number": str(cmd_obj.get("Sequence Number", "")),
                    "Attribute": TARGET_ATTR_NAMES[attr_key],
                    "Status": status_clean,
                    "Data Type": dtype_clean,
                    "Data Value": data_value,
                }
            )

    return extracted


def flatten_outgoing_cost_map(outgoing_cost_map):
    rows = []
    sources_sorted = sorted(outgoing_cost_map.keys(), key=lambda s: int(s, 16))
    for src in sources_sorted:
        destinations = outgoing_cost_map[src]
        dest_sorted = sorted(destinations.keys(), key=lambda d: int(d, 16))
        for dst in dest_sorted:
            rows.append({"Source": src, "Destination": dst, "Cost": destinations[dst]})
    return rows


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            row_copy = dict(row)
            if "No." in fieldnames and "No." not in row_copy:
                row_copy["No."] = idx
            writer.writerow(row_copy)


def main():
    default_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Generate Challenge 3 output CSV files from challenge3.csv")
    parser.add_argument("--input", default=str(default_root / "challenge3.csv"), help="Input challenge CSV")
    parser.add_argument("--outdir", default=str(default_root), help="Output directory")
    parser.add_argument("--messages", type=int, default=200, help="Number of ID messages to process")
    parser.add_argument("--seed", type=int, default=20260430, help="RNG seed for reproducibility")
    parser.add_argument("--start-ts", type=int, default=int(time.time()), help="Start UNIX timestamp")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows_by_packet = {}
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_by_packet[int(row["Packet Number"])] = row

    modulo = 5218

    rng = random.Random(args.seed)

    id_log_rows = []
    filtered_rows = []
    outgoing_cost_map = defaultdict(dict)

    zcl_publish_count = 0
    link_status_count = 0
    ignored_count = 0

    for msg_index in range(args.messages):
        msg_no = msg_index + 1
        id_value = rng.randint(0, 30000)
        timestamp = args.start_ts + msg_index
        packet_n = id_value % modulo

        id_log_rows.append({"No.": msg_no, "ID": id_value, "TIMESTAMP": timestamp})

        row = rows_by_packet.get(packet_n)
        if row is None:
            ignored_count += 1
            continue

        cmd_obj = parse_command_string(row.get("Command String", ""))
        has_zcl = isinstance(cmd_obj, dict) and ("Layer ZBEE_ZCL" in cmd_obj)
        is_link_status = row.get("Packet Type", "") == "Link Status (0x08)"

        if has_zcl:
            zcl_publish_count += 1
            extracted = extract_target_attributes(cmd_obj, timestamp)
            filtered_rows.extend(extracted)
        elif is_link_status:
            link_status_count += 1
            source_addr = normalize_hex_addr(row.get("Source Address ZigBee", ""))
            links = cmd_obj.get("Links", []) if isinstance(cmd_obj, dict) else []
            if isinstance(links, list):
                for link in links:
                    if not isinstance(link, dict):
                        continue
                    dest_addr = normalize_hex_addr(link.get("Address", ""))
                    if not source_addr or not dest_addr:
                        continue
                    outgoing_cost_map[source_addr][dest_addr] = str(link.get("Outgoing Cost", "")).strip()
        else:
            ignored_count += 1

    outgoing_rows = flatten_outgoing_cost_map(outgoing_cost_map)

    thingspeak_rows = []
    if outgoing_cost_map:
        smallest_source = sorted(outgoing_cost_map.keys(), key=lambda s: int(s, 16))[0]
        dest_sorted = sorted(outgoing_cost_map[smallest_source].keys(), key=lambda d: int(d, 16))
        for idx, dst in enumerate(dest_sorted, start=1):
            cost = outgoing_cost_map[smallest_source][dst]
            thingspeak_rows.append(
                {
                    "No.": idx,
                    "Source": smallest_source,
                    "Destination": dst,
                    "Cost": cost,
                    "Field1": cost,
                    "SendOffsetSec": (idx - 1) * 20,
                }
            )

    write_csv(
        outdir / "id_log.csv",
        ["No.", "ID", "TIMESTAMP"],
        id_log_rows,
    )

    write_csv(
        outdir / "filtered_elems.csv",
        ["No.", "Timestamp", "Sequence Number", "Attribute", "Status", "Data Type", "Data Value"],
        filtered_rows,
    )

    write_csv(
        outdir / "outgoing_cost.csv",
        ["No.", "Source", "Destination", "Cost"],
        outgoing_rows,
    )

    write_csv(
        outdir / "thingspeak_queue.csv",
        ["No.", "Source", "Destination", "Cost", "Field1", "SendOffsetSec"],
        thingspeak_rows,
    )

    summary = {
        "seed": args.seed,
        "start_timestamp": args.start_ts,
        "messages_processed": args.messages,
        "csv_packet_modulo": modulo,
        "zcl_messages": zcl_publish_count,
        "link_status_messages": link_status_count,
        "ignored_messages": ignored_count,
        "filtered_rows": len(filtered_rows),
        "outgoing_rows": len(outgoing_rows),
        "thingspeak_rows": len(thingspeak_rows),
        "smallest_source_for_thingspeak": thingspeak_rows[0]["Source"] if thingspeak_rows else None,
    }

    (outdir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
