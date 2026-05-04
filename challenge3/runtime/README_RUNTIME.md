# Challenge 3 Runtime (Docker)

This runtime starts:
- `challenge3-mosquitto` on `localhost:1884`
- `challenge3-node-red` on `http://localhost:1880`

It automatically copies `../nodered.txt` to `./node-red/flows.json` before startup.

## Start

```bash
cd /home/pitesse/Desktop/IoT/challenge3/runtime
chmod +x start_stack.sh stop_stack.sh
./start_stack.sh
```

## Verify

- Node-RED editor: `http://localhost:1880`
- Dashboard charts: `http://localhost:1880/ui`
- Mosquitto: `localhost:1884`

## Stop

```bash
./stop_stack.sh
```

