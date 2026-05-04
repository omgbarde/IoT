#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FLOW_PATH = ROOT / "nodered.txt"
ID_LOG = ROOT / "id_log.csv"
FILTERED = ROOT / "filtered_elems.csv"
OUTGOING = ROOT / "outgoing_cost.csv"


def load_flow():
    return json.loads(FLOW_PATH.read_text(encoding="utf-8"))


def by_type(nodes, t):
    return [n for n in nodes if n.get("type") == t]


def check(condition, name, details="", fails=None):
    if fails is None:
        fails = []
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"       {details}")
    if not condition:
        fails.append(name)


def csv_header(path):
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        return next(r, [])


def main():
    fails = []
    nodes = load_flow()

    mqtt_brokers = by_type(nodes, "mqtt-broker")
    local_broker = None
    for b in mqtt_brokers:
        host = str(b.get("broker", ""))
        port = str(b.get("port", ""))
        if (host, port) in {("localhost", "1884"), ("mosquitto", "1883")}:
            local_broker = b
            break
    check(local_broker is not None, "MQTT broker config is valid (localhost:1884 or docker mosquitto:1883)", fails=fails)

    inject_nodes = by_type(nodes, "inject")
    one_sec_gen = any(n.get("repeat") == "1" for n in inject_nodes)
    check(one_sec_gen, "Generator inject node repeats every 1 second", fails=fails)

    funcs = by_type(nodes, "function")
    func_text = "\n".join(n.get("func", "") for n in funcs)
    check("Math.random() * 30001" in func_text, "Random ID range uses 0..30000", fails=fails)
    check("((idInt % 5218) + 5218) % 5218" in func_text, "Modulo N uses fixed 5218", fails=fails)
    check("count >= 200" in func_text, "Subscriber hard-stop at 200 IDs", fails=fails)
    check("no >= 200" in func_text, "Generator also stops after 200 IDs", fails=fails)
    check("Layer ZBEE_ZCL" in func_text, "ZBEE_ZCL branch detection present", fails=fails)
    check("Link Status (0x08)" in func_text, "Link Status branch detection present", fails=fails)
    check("ThingSpeak key missing" in func_text, "ThingSpeak key handling present", fails=fails)
    check("toHex(addr)" in func_text and "if (!text.startsWith(\"0x\"))" in func_text, "Hex normalization helper present", fails=fails)

    mqtt_in_nodes = by_type(nodes, "mqtt in")
    mqtt_out_nodes = by_type(nodes, "mqtt out")
    check(any(n.get("topic") == "challenge3/id_generator" for n in mqtt_in_nodes), "MQTT subscription to challenge3/id_generator", fails=fails)
    check(any(n.get("topic") == "challenge3/id_generator" for n in mqtt_out_nodes), "MQTT publication to challenge3/id_generator", fails=fails)

    delays = by_type(nodes, "delay")
    rate_10_min = any(str(n.get("rate")) == "10" and str(n.get("rateUnits")) == "minute" for n in delays)
    rate_1_20s = any(str(n.get("rate")) == "1" and str(n.get("nbRateUnits")) == "20" and str(n.get("rateUnits")) == "second" for n in delays)
    check(rate_10_min, "Rate limiter 10 messages/minute exists for ZCL publish", fails=fails)
    check(rate_1_20s, "Rate limiter 1 message/20s exists for ThingSpeak", fails=fails)

    charts = by_type(nodes, "ui_chart")
    chart_labels = sorted([c.get("label", "") for c in charts])
    check("RMS Current" in chart_labels and "RMS Voltage" in chart_labels, "Both RMS Current and RMS Voltage charts exist", details=f"labels={chart_labels}", fails=fails)

    # CSV output checks
    check(ID_LOG.exists(), "id_log.csv exists", fails=fails)
    check(FILTERED.exists(), "filtered_elems.csv exists", fails=fails)
    check(OUTGOING.exists(), "outgoing_cost.csv exists", fails=fails)

    if ID_LOG.exists():
        header = csv_header(ID_LOG)
        check(header == ["No.", "ID", "TIMESTAMP"], "id_log.csv header format", details=str(header), fails=fails)
        rows = list(csv.DictReader(ID_LOG.open(newline="", encoding="utf-8")))
        seq_ok = all(int(r["No."]) == i + 1 for i, r in enumerate(rows))
        check(seq_ok, "id_log.csv row numbers incremental", details=f"rows={len(rows)}", fails=fails)
        check(len(rows) == 200, "id_log.csv contains exactly 200 data rows", details=f"rows={len(rows)}", fails=fails)

    if FILTERED.exists():
        header = csv_header(FILTERED)
        wanted = ["No.", "Timestamp", "Sequence Number", "Attribute", "Status", "Data Type", "Data Value"]
        check(header == wanted, "filtered_elems.csv header format", details=str(header), fails=fails)
        rows = list(csv.DictReader(FILTERED.open(newline="", encoding="utf-8")))
        attrs = {r["Attribute"] for r in rows}
        check(any(a == "RMS Current" for a in attrs), "filtered_elems.csv contains RMS Current rows", fails=fails)
        check(any(a == "RMS Voltage" for a in attrs), "filtered_elems.csv contains RMS Voltage rows", fails=fails)
        check(any(a == "Active Power" for a in attrs), "filtered_elems.csv contains Active Power rows", fails=fails)

    if OUTGOING.exists():
        header = csv_header(OUTGOING)
        check(header == ["No.", "Source", "Destination", "Cost"], "outgoing_cost.csv header format", details=str(header), fails=fails)
        rows = list(csv.DictReader(OUTGOING.open(newline="", encoding="utf-8")))
        hex_re = re.compile(r"^0x[0-9a-fA-F]+$")
        hex_ok = all(hex_re.match(r["Source"]) and hex_re.match(r["Destination"]) for r in rows)
        check(hex_ok, "outgoing_cost.csv addresses are hex formatted", details=f"rows={len(rows)}", fails=fails)

    print()
    if fails:
        print("FAILED checks:")
        for f in fails:
            print(f"- {f}")
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
