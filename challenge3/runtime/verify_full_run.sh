#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHALLENGE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${SCRIPT_DIR}"

ID_LOG="${CHALLENGE_DIR}/id_log.csv"
FILTERED="${CHALLENGE_DIR}/filtered_elems.csv"
OUTGOING="${CHALLENGE_DIR}/outgoing_cost.csv"
TS_QUEUE="${CHALLENGE_DIR}/thingspeak_queue.csv"
NR_LOG="${SCRIPT_DIR}/last_run_node_red.log"

if ! docker compose -f "${SCRIPT_DIR}/docker-compose.yml" ps --services --status running | grep -q '^node-red$'; then
  echo "node-red service is not running. Start the stack first with ./start_stack.sh"
  exit 1
fi

START_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Restarting Node-RED to start a clean 200-message run..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" restart node-red >/dev/null

echo "Waiting until id_log.csv reaches 200 data rows..."
export ID_LOG
python3 - <<'PY'
import os
import time
from pathlib import Path

id_path = Path(os.environ["ID_LOG"])
timeout_s = 320
start = time.time()
target = 201  # header + 200 rows

while True:
    lines = 0
    if id_path.exists():
        lines = sum(1 for _ in id_path.open())
    if lines >= target:
        print(f"Reached {lines} lines in id_log.csv")
        break
    if time.time() - start > timeout_s:
        raise SystemExit(f"Timeout: id_log.csv has {lines} lines (expected >= {target})")
    time.sleep(2)
PY

KEY="$(grep -E '^THINGSPEAK_WRITE_API_KEY=' "${SCRIPT_DIR}/.env" 2>/dev/null | cut -d'=' -f2- || true)"
if [ -n "${KEY}" ]; then
  echo "ThingSpeak key detected. Waiting 170 seconds for paced field1 sends (1 every 20s)..."
  sleep 170
else
  echo "ThingSpeak key is empty: skipping paced-send wait."
fi

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" logs --since "${START_TS}" node-red > "${NR_LOG}" 2>&1 || true

echo
echo "=== Output CSV line counts ==="
wc -l "${ID_LOG}" "${FILTERED}" "${OUTGOING}" "${TS_QUEUE}"

echo
echo "=== Validation checks ==="
python3 "${CHALLENGE_DIR}/verify_challenge3_requirements.py" || true

echo
echo "=== ThingSpeak-related logs from this run ==="
grep -E 'ThingSpeak key missing|debug:ThingSpeak response' "${NR_LOG}" || echo "No ThingSpeak log lines found."

echo
echo "Saved Node-RED run log to: ${NR_LOG}"
