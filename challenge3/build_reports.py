#!/usr/bin/env python3
import csv
import datetime as dt
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
SUMMARY_PATH = ROOT / 'run_summary.json'
FILTERED_PATH = ROOT / 'filtered_elems.csv'
OUTGOING_PATH = ROOT / 'outgoing_cost.csv'
ID_LOG_PATH = ROOT / 'id_log.csv'
THINGSPEAK_QUEUE_PATH = ROOT / 'thingspeak_queue.csv'
FLOW_JSON_PATH = ROOT / 'nodered.txt'

FLOW_IMG = ROOT / 'nodered_flow_diagram.png'
RMS_CURR_IMG = ROOT / 'rms_current_chart.png'
RMS_VOLT_IMG = ROOT / 'rms_voltage_chart.png'

CHALLENGE_PDF = ROOT / 'Challenge.pdf'
EXERCISE_PDF = ROOT / 'Exercise.pdf'
FORM_VALUES_TXT = ROOT / 'FORM_VALUES.txt'

TEAM_NAME_PLACEHOLDER = 'YOUR NAME SURNAME + TEAMMATE NAME SURNAME'
TEAM_CODE_PLACEHOLDER = 'PERSONCODE1 + PERSONCODE2'


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def draw_flow_diagram(output_path: Path):
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.axis('off')

    boxes = [
        ('Init + Load CSV', (0.05, 0.75), '#d7f0ff'),
        ('Generate ID\n1 msg/s', (0.05, 0.45), '#d9f7d9'),
        ('MQTT Publish\nchallenge3/id_generator', (0.28, 0.45), '#fff3cd'),
        ('MQTT Subscribe\nchallenge3/id_generator', (0.28, 0.23), '#fff3cd'),
        ('Compute N = ID mod 5218\nLookup Packet N', (0.52, 0.23), '#ffe1cc'),
        ('ZBEE_ZCL branch\nPublish (10/min)', (0.78, 0.38), '#f8d7ff'),
        ('Filtered attributes\n+ CSV + Charts', (0.78, 0.20), '#f8d7ff'),
        ('Link Status branch\nUpdate outgoing map', (0.52, 0.05), '#ffd7d7'),
        ('At 200 IDs:\noutgoing_cost.csv + ThingSpeak queue', (0.78, 0.05), '#ffd7d7'),
    ]

    width, height = 0.2, 0.12
    positions = {}

    for label, (x, y), color in boxes:
        box = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle='round,pad=0.02,rounding_size=0.02',
            linewidth=1.5,
            edgecolor='#333333',
            facecolor=color,
        )
        ax.add_patch(box)
        ax.text(x + width / 2, y + height / 2, label, ha='center', va='center', fontsize=10)
        positions[label] = (x + width / 2, y + height / 2)

    def arrow(src_label, dst_label):
        sx, sy = positions[src_label]
        dx, dy = positions[dst_label]
        patch = FancyArrowPatch(
            (sx + 0.10, sy),
            (dx - 0.10, dy),
            arrowstyle='->',
            mutation_scale=14,
            linewidth=1.5,
            color='#333333',
            connectionstyle='arc3,rad=0.0',
        )
        ax.add_patch(patch)

    arrow('Init + Load CSV', 'Compute N = ID mod 5218\nLookup Packet N')
    arrow('Generate ID\n1 msg/s', 'MQTT Publish\nchallenge3/id_generator')
    arrow('MQTT Publish\nchallenge3/id_generator', 'MQTT Subscribe\nchallenge3/id_generator')
    arrow('MQTT Subscribe\nchallenge3/id_generator', 'Compute N = ID mod 5218\nLookup Packet N')
    arrow('Compute N = ID mod 5218\nLookup Packet N', 'ZBEE_ZCL branch\nPublish (10/min)')
    arrow('Compute N = ID mod 5218\nLookup Packet N', 'Filtered attributes\n+ CSV + Charts')
    arrow('Compute N = ID mod 5218\nLookup Packet N', 'Link Status branch\nUpdate outgoing map')
    arrow('Link Status branch\nUpdate outgoing map', 'At 200 IDs:\noutgoing_cost.csv + ThingSpeak queue')

    ax.set_title('Node-RED Challenge 3 Logical Flow', fontsize=16, pad=16)
    plt.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def draw_rms_charts(filtered_rows, current_img: Path, voltage_img: Path):
    current_points = []
    voltage_points = []

    for row in filtered_rows:
        attr = row.get('Attribute', '').strip()
        val = row.get('Data Value', '').strip()
        ts = row.get('Timestamp', '').strip()
        if not ts or not val:
            continue
        try:
            t = dt.datetime.fromtimestamp(int(ts))
            y = int(val)
        except ValueError:
            continue

        if attr == 'RMS Current':
            current_points.append((t, y))
        elif attr == 'RMS Voltage':
            voltage_points.append((t, y))

    def plot_series(points, title, ylabel, out_path, color):
        fig, ax = plt.subplots(figsize=(10, 4.2))
        stats = {
            'count': 0,
            'min': None,
            'max': None,
            'unique_count': 0,
            'unique_values': [],
            'is_flat': False,
        }
        if points:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, marker='o', linewidth=1.8, color=color)
            uniq = sorted(set(ys))
            stats.update(
                {
                    'count': len(ys),
                    'min': min(ys),
                    'max': max(ys),
                    'unique_count': len(uniq),
                    'unique_values': uniq,
                    'is_flat': len(uniq) == 1,
                }
            )
            if len(uniq) == 1:
                ax.text(
                    0.02,
                    0.92,
                    f'All observed values are {uniq[0]}',
                    transform=ax.transAxes,
                    fontsize=10,
                    bbox={'facecolor': 'white', 'alpha': 0.75, 'edgecolor': '#999999'},
                )
        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        plt.tight_layout()
        fig.savefig(out_path, dpi=180)
        plt.close(fig)
        return stats

    current_stats = plot_series(current_points, 'RMS Current Values', 'Current', current_img, '#1f77b4')
    voltage_stats = plot_series(voltage_points, 'RMS Voltage Values', 'Voltage', voltage_img, '#d62728')
    return {'current': current_stats, 'voltage': voltage_stats}


def first_rows_table(rows, wanted_columns, n=8):
    header = wanted_columns
    data = [header]
    for row in rows[:n]:
        data.append([str(row.get(c, '')) for c in header])
    return data


def build_challenge_pdf(summary, filtered_rows, outgoing_rows, id_rows, chart_stats):
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('IoT Challenge #3 - Node-RED Report', styles['Title']))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f'Team: {TEAM_NAME_PLACEHOLDER}', styles['Normal']))
    story.append(Paragraph(f'Person codes: {TEAM_CODE_PLACEHOLDER}', styles['Normal']))
    story.append(Paragraph('Date: 30 April 2026', styles['Normal']))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph('1) Implementation overview', styles['Heading2']))
    overview = (
        'The Node-RED flow publishes one random ID per second to the local broker '
        '(localhost:1884, topic challenge3/id_generator), subscribes to the same topic, computes '
        'N = ID mod 5218, and processes packet N from challenge3.csv. '
        'ZBEE_ZCL packets are republished with the required payload and rate-limited at 10 messages/minute; '
        'RMS/Active Power attributes are extracted to filtered_elems.csv and plotted on dashboard charts. '
        'Link Status packets update outgoing link costs; at exactly 200 received IDs the flow stops, writes '
        'outgoing_cost.csv, and builds the ThingSpeak queue ordered by destination address.'
    )
    story.append(Paragraph(overview, styles['BodyText']))
    story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph('2) Node-RED flow image', styles['Heading2']))
    story.append(Image(str(FLOW_IMG), width=17.5 * cm, height=9.2 * cm))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph('3) Main node blocks and meaning', styles['Heading2']))
    nodes_text = (
        'A. Init + Load CSV: resets counters/context and writes CSV headers.\n'
        'B. Generator branch: creates random IDs [0..30000], JSON payload, and id_log rows.\n'
        'C. Subscription branch: counts incoming IDs (hard stop at 200) and computes modulo index N.\n'
        'D. ZBEE_ZCL branch: builds required publish payload and enforces 10/min rate limit.\n'
        'E. Filter branch: extracts Active Power / RMS Current / RMS Voltage with positional matching and logs CSV rows.\n'
        'F. Link Status branch: updates per-source per-destination outgoing cost map.\n'
        'G. Finalization branch: writes outgoing_cost.csv and queues ThingSpeak HTTP updates every 20s.'
    )
    for line in nodes_text.split('\n'):
        story.append(Paragraph(line, styles['BodyText']))

    story.append(PageBreak())

    story.append(Paragraph('4) Generated output summary (200-message run)', styles['Heading2']))
    summary_table = Table(
        [
            ['Metric', 'Value'],
            ['Seed', str(summary.get('seed'))],
            ['Start timestamp', str(summary.get('start_timestamp'))],
            ['Messages processed', str(summary.get('messages_processed'))],
            ['ZBEE_ZCL packets', str(summary.get('zcl_messages'))],
            ['Link Status packets', str(summary.get('link_status_messages'))],
            ['Ignored packets', str(summary.get('ignored_messages'))],
            ['filtered_elems rows', str(summary.get('filtered_rows'))],
            ['outgoing_cost rows', str(summary.get('outgoing_rows'))],
            ['ThingSpeak queue rows', str(summary.get('thingspeak_rows'))],
            ['Smallest source (ThingSpeak)', str(summary.get('smallest_source_for_thingspeak'))],
        ],
        colWidths=[7 * cm, 8.5 * cm],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph('5) CSV excerpts', styles['Heading2']))

    story.append(Paragraph('id_log.csv (first rows)', styles['Heading3']))
    tbl_id = Table(first_rows_table(id_rows, ['No.', 'ID', 'TIMESTAMP'], n=8), colWidths=[2 * cm, 3.5 * cm, 4.5 * cm])
    tbl_id.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)]))
    story.append(tbl_id)
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph('filtered_elems.csv (first rows)', styles['Heading3']))
    tbl_filtered = Table(
        first_rows_table(filtered_rows, ['No.', 'Timestamp', 'Sequence Number', 'Attribute', 'Status', 'Data Type', 'Data Value'], n=8),
        colWidths=[1.2 * cm, 2.6 * cm, 2.0 * cm, 2.4 * cm, 1.8 * cm, 4.0 * cm, 1.5 * cm],
    )
    tbl_filtered.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)]))
    story.append(tbl_filtered)
    story.append(Spacer(1, 0.2 * cm))

    tbl_outgoing = Table(first_rows_table(outgoing_rows, ['No.', 'Source', 'Destination', 'Cost'], n=8), colWidths=[1.5 * cm, 3 * cm, 3 * cm, 2 * cm])
    tbl_outgoing.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)]))
    story.append(tbl_outgoing)

    story.append(PageBreak())

    story.append(Paragraph('6) RMS chart outputs', styles['Heading2']))
    story.append(
        Paragraph(
            (
                f"RMS Current samples: {chart_stats['current']['count']}, "
                f"unique values: {chart_stats['current']['unique_values']}. "
                f"RMS Voltage samples: {chart_stats['voltage']['count']}, "
                f"unique values: {chart_stats['voltage']['unique_values']}."
            ),
            styles['BodyText'],
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph('RMS Current chart', styles['Heading3']))
    story.append(Image(str(RMS_CURR_IMG), width=17.5 * cm, height=7 * cm))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph('RMS Voltage chart', styles['Heading3']))
    story.append(Image(str(RMS_VOLT_IMG), width=17.5 * cm, height=7 * cm))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph('7) ThingSpeak channel note', styles['Heading2']))
    story.append(
        Paragraph(
            'Flow includes ThingSpeak HTTP updates every 20 seconds in destination-address order. '
            'Set flow.thingspeak_write_api_key (or THINGSPEAK_WRITE_API_KEY) and add the public channel URL here before final submission: '
            '<b>TO_BE_FILLED_WITH_PUBLIC_CHANNEL_LINK</b>.',
            styles['BodyText'],
        )
    )

    doc = SimpleDocTemplate(str(CHALLENGE_PDF), pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    doc.build(story)


def compute_lora_table():
    bw = 125000
    pl = 20
    crc = 1
    h = 0
    n_preamble = 8
    cr = 1  # 4/5
    lam = 40 * 2 / 60  # packets per second

    rows = []
    for sf in range(7, 13):
        de = 1 if sf >= 11 else 0
        t_sym = (2 ** sf) / bw
        numerator = 8 * pl - 4 * sf + 28 + 16 * crc - 20 * h
        denominator = 4 * (sf - 2 * de)
        payload_symbols = 8 + max(math.ceil(numerator / denominator) * (cr + 4), 0)
        t_preamble = (n_preamble + 4.25) * t_sym
        t_payload = payload_symbols * t_sym
        airtime = t_preamble + t_payload
        p_success = math.exp(-2 * lam * airtime)
        rows.append({'SF': sf, 'Airtime_ms': airtime * 1000, 'Success': p_success})
    return rows


def build_exercise_pdf():
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('IoT Challenge #3 - Exercise (LoRaWAN)', styles['Title']))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f'Team: {TEAM_NAME_PLACEHOLDER}', styles['Normal']))
    story.append(Paragraph(f'Person codes: {TEAM_CODE_PLACEHOLDER}', styles['Normal']))
    story.append(Paragraph('Date: 30 April 2026', styles['Normal']))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph('EQ1 - Largest SF with packet success rate >= 75%', styles['Heading2']))
    assumptions = (
        'Assumptions: EU868, BW=125 kHz, payload=20 B, coding rate 4/5, explicit header, CRC on, '
        'single gateway, all 40 nodes use the same SF, and uncoordinated transmissions (pure-ALOHA overlap model). '
        'Total offered traffic lambda = 40 * 2 / 60 = 1.333 packets/s. '
        'For packet airtime T, success probability is approximated as P_success = exp(-2 * lambda * T).'
    )
    story.append(Paragraph(assumptions, styles['BodyText']))
    story.append(Spacer(1, 0.2 * cm))

    table_rows = compute_lora_table()
    data = [['SF', 'Airtime [ms]', 'P_success']] + [
        [str(r['SF']), f"{r['Airtime_ms']:.3f}", f"{r['Success']:.3f}"] for r in table_rows
    ]
    t = Table(data, colWidths=[2.5 * cm, 4 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * cm))

    story.append(
        Paragraph(
            '<b>Answer EQ1:</b> the largest spreading factor that still guarantees at least 75% success '
            'is <b>SF8</b> (P_success ~ 0.760). SF9 drops to ~0.610, below the 75% target.',
            styles['BodyText'],
        )
    )

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph('EQ2 - Best corrective action in field deployment', styles['Heading2']))
    story.append(
        Paragraph(
            '<b>Selected action: 2) Move the nodes closer to the gateway.</b><br/>'
            'Reason: the measured behavior is heterogeneous (some nodes good, some poor), which is typical of '
            'link-budget and radio-coverage differences across positions. Bringing weak nodes closer improves '
            'SNR/path loss and reduces packet loss for the worst nodes. Increasing SF would increase airtime and '
            'collision probability for everyone, while decreasing node count is not a deployment fix and does not '
            'directly address location-dependent weak links.',
            styles['BodyText'],
        )
    )

    doc = SimpleDocTemplate(str(EXERCISE_PDF), pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm)
    doc.build(story)


def build_form_values(summary, filtered_rows, outgoing_rows, thingspeak_rows, chart_stats):
    lines = []
    lines.append('Challenge #3 - Form helper values')
    lines.append('')
    lines.append(f"Run seed: {summary.get('seed')}")
    lines.append(f"Run start timestamp: {summary.get('start_timestamp')}")
    lines.append(f"IDs processed: {summary.get('messages_processed')}")
    lines.append('')
    lines.append('CSV sizes:')
    lines.append(f"- id_log.csv rows: {len(read_csv(ID_LOG_PATH))}")
    lines.append(f"- filtered_elems.csv rows: {len(filtered_rows)}")
    lines.append(f"- outgoing_cost.csv rows: {len(outgoing_rows)}")
    lines.append('')
    lines.append('RMS chart sanity check:')
    lines.append(f"- RMS Current unique values: {chart_stats['current']['unique_values']}")
    lines.append(f"- RMS Voltage unique values: {chart_stats['voltage']['unique_values']}")
    lines.append('')
    lines.append('Smallest source address in outgoing_cost.csv:')
    lines.append(f"- {summary.get('smallest_source_for_thingspeak')}")
    lines.append('')
    lines.append('ThingSpeak ordered queue (Destination -> Cost):')
    for row in thingspeak_rows:
        lines.append(f"- {row['Destination']} -> {row['Cost']} (field1={row['Field1']}, send at +{row['SendOffsetSec']}s)")
    lines.append('')
    lines.append('First 10 rows of filtered_elems.csv:')
    for row in filtered_rows[:10]:
        lines.append(','.join([
            row.get('No.', ''),
            row.get('Timestamp', ''),
            row.get('Sequence Number', ''),
            row.get('Attribute', ''),
            row.get('Status', ''),
            row.get('Data Type', ''),
            row.get('Data Value', ''),
        ]))
    lines.append('')
    lines.append('First 10 rows of outgoing_cost.csv:')
    for row in outgoing_rows[:10]:
        lines.append(','.join([
            row.get('No.', ''),
            row.get('Source', ''),
            row.get('Destination', ''),
            row.get('Cost', ''),
        ]))
    lines.append('')
    lines.append('ThingSpeak public channel URL: TO_BE_FILLED')

    FORM_VALUES_TXT.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    summary = json.loads(SUMMARY_PATH.read_text(encoding='utf-8'))
    filtered_rows = read_csv(FILTERED_PATH)
    outgoing_rows = read_csv(OUTGOING_PATH)
    id_rows = read_csv(ID_LOG_PATH)
    thingspeak_rows = read_csv(THINGSPEAK_QUEUE_PATH)

    draw_flow_diagram(FLOW_IMG)
    chart_stats = draw_rms_charts(filtered_rows, RMS_CURR_IMG, RMS_VOLT_IMG)
    build_challenge_pdf(summary, filtered_rows, outgoing_rows, id_rows, chart_stats)
    build_exercise_pdf()
    build_form_values(summary, filtered_rows, outgoing_rows, thingspeak_rows, chart_stats)

    print('Generated:')
    print('-', FLOW_IMG)
    print('-', RMS_CURR_IMG)
    print('-', RMS_VOLT_IMG)
    print('-', CHALLENGE_PDF)
    print('-', EXERCISE_PDF)
    print('-', FORM_VALUES_TXT)


if __name__ == '__main__':
    main()
