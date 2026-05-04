#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHALLENGE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${SCRIPT_DIR}"

mkdir -p "${SCRIPT_DIR}/mosquitto/data" "${SCRIPT_DIR}/mosquitto/log" "${SCRIPT_DIR}/node-red"

# Always load the latest exported flow into Node-RED runtime.
cp "${CHALLENGE_DIR}/nodered.txt" "${SCRIPT_DIR}/node-red/flows.json"

if [ ! -f "${SCRIPT_DIR}/.env" ]; then
  cat > "${SCRIPT_DIR}/.env" <<'EOF'
NODERED_PORT=1880
MOSQUITTO_PORT=1884
THINGSPEAK_WRITE_API_KEY=
EOF
fi

ensure_env_var() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${SCRIPT_DIR}/.env"; then
    echo "${key}=${value}" >> "${SCRIPT_DIR}/.env"
  fi
}

ensure_env_var "NODERED_PORT" "1880"
ensure_env_var "MOSQUITTO_PORT" "1884"
ensure_env_var "THINGSPEAK_WRITE_API_KEY" ""

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/.env"
NODERED_PORT="${NODERED_PORT:-1880}"
MOSQUITTO_PORT="${MOSQUITTO_PORT:-1884}"

docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d

# Install dashboard nodes on first run, then restart Node-RED so ui_* nodes are available.
if [ ! -d "${SCRIPT_DIR}/node-red/node_modules/node-red-dashboard" ]; then
  echo "Installing node-red-dashboard in container..."
  for _ in $(seq 1 30); do
    if docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T node-red sh -lc "true" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  docker compose -f "${SCRIPT_DIR}/docker-compose.yml" exec -T node-red sh -lc "cd /data && npm install --no-update-notifier --no-fund node-red-dashboard@^3.6.5"
  docker compose -f "${SCRIPT_DIR}/docker-compose.yml" restart node-red >/dev/null
fi

echo
echo "Stack started."
echo "Node-RED editor: http://localhost:${NODERED_PORT}"
echo "Node-RED dashboard: http://localhost:${NODERED_PORT}/ui"
echo "Mosquitto broker: localhost:${MOSQUITTO_PORT}"
echo
echo "Useful commands:"
echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml logs -f node-red"
echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml logs -f mosquitto"
echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml ps"
