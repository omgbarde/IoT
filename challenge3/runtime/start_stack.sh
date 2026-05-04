#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHALLENGE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

mkdir -p "${SCRIPT_DIR}/mosquitto/data" "${SCRIPT_DIR}/mosquitto/log" "${SCRIPT_DIR}/node-red"

# Always load the latest exported flow into Node-RED runtime.
cp "${CHALLENGE_DIR}/nodered.txt" "${SCRIPT_DIR}/node-red/flows.json"

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d

# Install dashboard nodes on first run, then restart Node-RED so ui_* nodes are available.
if [ ! -d "${SCRIPT_DIR}/node-red/node_modules/node-red-dashboard" ]; then
  echo "Installing node-red-dashboard in container..."
  docker exec challenge3-node-red sh -lc "cd /data && npm install --no-update-notifier --no-fund node-red-dashboard@^3.6.5"
  docker restart challenge3-node-red >/dev/null
fi

echo
echo "Stack started."
echo "Node-RED editor: http://localhost:1880"
echo "Node-RED dashboard: http://localhost:1880/ui"
echo "Mosquitto broker: localhost:1884"
echo
echo "Useful commands:"
echo "  docker logs -f challenge3-node-red"
echo "  docker logs -f challenge3-mosquitto"
echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml ps"
