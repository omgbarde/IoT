#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <THINGSPEAK_WRITE_API_KEY>"
  exit 1
fi

KEY="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
cd "${SCRIPT_DIR}"

touch "${ENV_FILE}"
grep -v '^THINGSPEAK_WRITE_API_KEY=' "${ENV_FILE}" > "${ENV_FILE}.tmp" || true
echo "THINGSPEAK_WRITE_API_KEY=${KEY}" >> "${ENV_FILE}.tmp"
mv "${ENV_FILE}.tmp" "${ENV_FILE}"

echo "Saved ThingSpeak write key to ${ENV_FILE}"
echo "Recreating Node-RED container to apply env..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" up -d --force-recreate node-red >/dev/null
echo "Node-RED recreated."
