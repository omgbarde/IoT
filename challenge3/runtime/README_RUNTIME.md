# Challenge 3 Runtime (Docker)

This runtime starts:
- Mosquitto on `localhost:${MOSQUITTO_PORT}` (default `1884`)
- Node-RED on `http://localhost:${NODERED_PORT}` (default `1880`)

It automatically copies `../nodered.txt` to `./node-red/flows.json` before startup.
It is cross-platform (Linux/macOS/Windows with Docker Desktop): no hardcoded host paths and no `network_mode: host`.

## Start

```bash
cd challenge3/runtime
chmod +x start_stack.sh stop_stack.sh set_thingspeak_key.sh verify_full_run.sh
./start_stack.sh
```

You can customize ports by editing `runtime/.env`:

```env
NODERED_PORT=1880
MOSQUITTO_PORT=1884
THINGSPEAK_WRITE_API_KEY=
```

If your ports are busy on another machine, change `NODERED_PORT` and/or `MOSQUITTO_PORT` in `.env` and run `./start_stack.sh` again.

## Verify

- Node-RED editor: `http://localhost:<NODERED_PORT>`
- Dashboard charts: `http://localhost:<NODERED_PORT>/ui`
- Mosquitto: `localhost:<MOSQUITTO_PORT>`

## Configure ThingSpeak key

```bash
./set_thingspeak_key.sh YOUR_WRITE_API_KEY
```

The flow reads `THINGSPEAK_WRITE_API_KEY` from `runtime/.env`.

## Full verification run

```bash
./verify_full_run.sh
```

This script:
1. Restarts Node-RED (fresh run).
2. Waits for 200 processed IDs.
3. If ThingSpeak key is configured, waits for paced sends (every 20s).
4. Prints CSV counts and challenge checks.
5. Stores run logs in `runtime/last_run_node_red.log`.

## Stop

```bash
./stop_stack.sh
```
