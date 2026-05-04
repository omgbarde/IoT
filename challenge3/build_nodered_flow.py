#!/usr/bin/env python3
import json
from pathlib import Path

FLOW_ID = "f3c8c0e1b9a2419e"
BROKER_ID = "a8f2c3d4e5f60718"
UI_TAB_ID = "b1c2d3e4f5a60718"
UI_GROUP_ID = "c1d2e3f4a5b60718"
CONTAINER_CHALLENGE_DIR = "/workspace/challenge3"
CSV_PATH = f"{CONTAINER_CHALLENGE_DIR}/challenge3.csv"
ID_LOG_PATH = f"{CONTAINER_CHALLENGE_DIR}/id_log.csv"
FILTERED_PATH = f"{CONTAINER_CHALLENGE_DIR}/filtered_elems.csv"
OUTGOING_PATH = f"{CONTAINER_CHALLENGE_DIR}/outgoing_cost.csv"
MQTT_BROKER_HOST = "mosquitto"
MQTT_BROKER_PORT = "1883"


def fn(text: str) -> str:
    return text.strip("\n")


nodes = [
    {
        "id": FLOW_ID,
        "type": "tab",
        "label": "Challenge3 Flow",
        "disabled": False,
        "info": "IoT Challenge #3 - Node-RED + LoRaWAN",
    },
    {
        "id": "e1a2b3c4d5f60718",
        "type": "comment",
        "z": FLOW_ID,
        "name": "Init + Load CSV",
        "info": "Resets runtime state, writes CSV headers, then loads challenge3.csv into memory.",
        "x": 160,
        "y": 60,
        "wires": [],
    },
    {
        "id": "f1a2b3c4d5e60718",
        "type": "inject",
        "z": FLOW_ID,
        "name": "Init once",
        "props": [{"p": "payload"}],
        "repeat": "",
        "crontab": "",
        "once": True,
        "onceDelay": "0.5",
        "topic": "",
        "payload": "",
        "payloadType": "date",
        "x": 150,
        "y": 100,
        "wires": [["a1b2c3d4e5f60718"]],
    },
    {
        "id": "a1b2c3d4e5f60718",
        "type": "function",
        "z": FLOW_ID,
        "name": "Init state + CSV headers",
        "func": fn(
            """
            flow.set("done", false);
            flow.set("subCount", 0);
            flow.set("idNo", 0);
            flow.set("filteredNo", 0);
            flow.set("outgoingCostMap", {});
            flow.set("csvIndex", {});

            return [
              { payload: Date.now() },
              { payload: "No.,ID,TIMESTAMP\\n" },
              { payload: "No.,Timestamp,Sequence Number,Attribute,Status,Data Type,Data Value\\n" },
              { payload: "No.,Source,Destination,Cost\\n" }
            ];
            """
        ),
        "outputs": 4,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 390,
        "y": 100,
        "wires": [
            ["a2b3c4d5e6f70182"],
            ["a3b4c5d6e7f80192"],
            ["a4b5c6d7e8f901a2"],
            ["a5b6c7d8e9f001b2"],
        ],
    },
    {
        "id": "a2b3c4d5e6f70182",
        "type": "file in",
        "z": FLOW_ID,
        "name": "Read challenge3.csv",
        "filename": CSV_PATH,
        "filenameType": "str",
        "format": "utf8",
        "chunk": False,
        "sendError": False,
        "encoding": "none",
        "allProps": False,
        "x": 620,
        "y": 100,
        "wires": [["a6b7c8d9e0f102c2"]],
    },
    {
        "id": "a6b7c8d9e0f102c2",
        "type": "csv",
        "z": FLOW_ID,
        "name": "CSV to objects",
        "sep": ",",
        "hdrin": True,
        "hdrout": "none",
        "multi": "one",
        "ret": "\\n",
        "temp": "",
        "skip": "0",
        "strings": True,
        "include_empty_strings": "",
        "include_null_values": "",
        "x": 840,
        "y": 100,
        "wires": [["a7b8c9d0e1f203d2"]],
    },
    {
        "id": "a7b8c9d0e1f203d2",
        "type": "function",
        "z": FLOW_ID,
        "name": "Index rows by Packet Number",
        "func": fn(
            """
            let rows;
            let index = flow.get("csvIndex") || {};

            if (Array.isArray(msg.payload)) {
              rows = msg.payload;
              index = {};
            } else {
              rows = [msg.payload];
            }

            for (const row of rows) {
              if (!row) {
                continue;
              }
              const n = Number(row["Packet Number"]);
              if (Number.isFinite(n)) {
                index[n] = row;
              }
            }

            const count = Object.keys(index).length;
            flow.set("csvIndex", index);

            return { payload: `CSV index ready: ${count} rows` };
            """
        ),
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 1090,
        "y": 100,
        "wires": [["a8b9c0d1e2f304e2"]],
    },
    {
        "id": "a8b9c0d1e2f304e2",
        "type": "debug",
        "z": FLOW_ID,
        "name": "CSV loaded",
        "active": True,
        "tosidebar": True,
        "console": False,
        "tostatus": False,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 1310,
        "y": 100,
        "wires": [],
    },
    {
        "id": "a3b4c5d6e7f80192",
        "type": "file",
        "z": FLOW_ID,
        "name": "Init id_log.csv",
        "filename": ID_LOG_PATH,
        "filenameType": "str",
        "appendNewline": False,
        "createDir": False,
        "overwriteFile": "true",
        "encoding": "none",
        "x": 620,
        "y": 160,
        "wires": [[]],
    },
    {
        "id": "a4b5c6d7e8f901a2",
        "type": "file",
        "z": FLOW_ID,
        "name": "Init filtered_elems.csv",
        "filename": FILTERED_PATH,
        "filenameType": "str",
        "appendNewline": False,
        "createDir": False,
        "overwriteFile": "true",
        "encoding": "none",
        "x": 640,
        "y": 200,
        "wires": [[]],
    },
    {
        "id": "a5b6c7d8e9f001b2",
        "type": "file",
        "z": FLOW_ID,
        "name": "Init outgoing_cost.csv",
        "filename": OUTGOING_PATH,
        "filenameType": "str",
        "appendNewline": False,
        "createDir": False,
        "overwriteFile": "true",
        "encoding": "none",
        "x": 640,
        "y": 240,
        "wires": [[]],
    },
    {
        "id": "f2a3b4c5d6e70819",
        "type": "comment",
        "z": FLOW_ID,
        "name": "ID generator + id_log.csv",
        "info": "Publishes 1 JSON message/sec to challenge3/id_generator and logs IDs to CSV.",
        "x": 180,
        "y": 320,
        "wires": [],
    },
    {
        "id": "b1c2d3e4f5a60729",
        "type": "inject",
        "z": FLOW_ID,
        "name": "Generate each 1s",
        "props": [{"p": "payload"}],
        "repeat": "1",
        "crontab": "",
        "once": True,
        "onceDelay": "2",
        "topic": "",
        "payload": "",
        "payloadType": "date",
        "x": 150,
        "y": 360,
        "wires": [["b2c3d4e5f6a70839"]],
    },
    {
        "id": "b2c3d4e5f6a70839",
        "type": "function",
        "z": FLOW_ID,
        "name": "Generate ID + log line",
        "func": fn(
            """
            if (flow.get("done")) {
              return [null, null];
            }

            let no = flow.get("idNo") || 0;
            if (no >= 200) {
              flow.set("done", true);
              return [null, null];
            }
            no += 1;
            flow.set("idNo", no);

            const id = Math.floor(Math.random() * 30001);
            const ts = Math.floor(Date.now() / 1000);
            const payload = { id, timestamp: ts };

            return [
              { topic: "challenge3/id_generator", payload: JSON.stringify(payload) },
              { payload: `${no},${id},${ts}\\n` }
            ];
            """
        ),
        "outputs": 2,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 390,
        "y": 360,
        "wires": [["b3c4d5e6f7a80949"], ["b4c5d6e7f8a90159"]],
    },
    {
        "id": "b3c4d5e6f7a80949",
        "type": "mqtt out",
        "z": FLOW_ID,
        "name": "Publish ID",
        "topic": "challenge3/id_generator",
        "qos": "0",
        "retain": "",
        "respTopic": "",
        "contentType": "",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": BROKER_ID,
        "x": 610,
        "y": 340,
        "wires": [],
    },
    {
        "id": "b4c5d6e7f8a90159",
        "type": "file",
        "z": FLOW_ID,
        "name": "Append id_log.csv",
        "filename": ID_LOG_PATH,
        "filenameType": "str",
        "appendNewline": False,
        "createDir": False,
        "overwriteFile": "false",
        "encoding": "none",
        "x": 620,
        "y": 380,
        "wires": [[]],
    },
    {
        "id": "f3a4b5c6d7e80919",
        "type": "comment",
        "z": FLOW_ID,
        "name": "Subscribe + Process 200 IDs",
        "info": "Processes each subscribed ID, computes N=ID mod 5218, handles ZCL/Link Status/Ignore, and finalizes outputs at 200.",
        "x": 190,
        "y": 460,
        "wires": [],
    },
    {
        "id": "c1d2e3f4a5b60729",
        "type": "mqtt in",
        "z": FLOW_ID,
        "name": "Subscribe ID topic",
        "topic": "challenge3/id_generator",
        "qos": "0",
        "datatype": "auto",
        "broker": BROKER_ID,
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 170,
        "y": 500,
        "wires": [["c2d3e4f5a6b70839"]],
    },
    {
        "id": "c2d3e4f5a6b70839",
        "type": "function",
        "z": FLOW_ID,
        "name": "Count <= 200 + compute N",
        "func": fn(
            """
            if (flow.get("done")) {
              return null;
            }

            let data = msg.payload;
            if (typeof data === "string") {
              try {
                data = JSON.parse(data);
              } catch (e) {
                return null;
              }
            }

            if (typeof data !== "object" || data === null || data.id === undefined) {
              return null;
            }

            const id = Number(data.id);
            if (!Number.isFinite(id)) {
              return null;
            }

            let count = flow.get("subCount") || 0;
            count += 1;
            flow.set("subCount", count);

            if (count >= 200) {
              flow.set("done", true);
            }

            const idInt = Math.trunc(id);

            msg.sub_id = idInt;
            msg.sub_timestamp = Number.isFinite(Number(data.timestamp))
              ? Math.trunc(Number(data.timestamp))
              : Math.floor(Date.now() / 1000);
            msg.sub_count = count;
            msg.n = ((idInt % 5218) + 5218) % 5218;

            return msg;
            """
        ),
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 430,
        "y": 500,
        "wires": [["c3d4e5f6a7b80949"]],
    },
    {
        "id": "c3d4e5f6a7b80949",
        "type": "function",
        "z": FLOW_ID,
        "name": "Process packet + outputs",
        "func": fn(
            """
            const packetIndex = flow.get("csvIndex");
            if (!packetIndex || Object.keys(packetIndex).length === 0) {
              node.warn("CSV index not ready yet");
              return [null, null, null, null, null, null, null];
            }

            const packet = packetIndex[msg.n];
            if (!packet) {
              return [null, null, null, null, null, null, null];
            }

            function parseCommand(raw) {
              const text = String(raw || "").trim();
              if (!text) {
                return {};
              }
              try {
                return Function(`"use strict"; return (${text});`)();
              } catch (e) {
                return {};
              }
            }

            function toHex(addr) {
              let text = String(addr || "").trim().toLowerCase();
              if (!text) {
                return "";
              }
              if (!text.startsWith("0x")) {
                if (/^[0-9a-f]+$/.test(text)) {
                  text = `0x${text}`;
                } else {
                  return text;
                }
              }
              const n = parseInt(text, 16);
              if (Number.isNaN(n)) {
                return text;
              }
              const digits = n.toString(16);
              const width = Math.max(4, digits.length);
              return `0x${digits.padStart(width, "0")}`;
            }

            function cleanLabel(v) {
              return String(v || "")
                .replace(/\\s*\\(0x[0-9a-fA-F]+\\)\\s*$/, "")
                .trim();
            }

            function asArray(v) {
              if (Array.isArray(v)) {
                return v;
              }
              if (v === undefined || v === null || v === "") {
                return [];
              }
              return [v];
            }

            function pickByIndex(arr, i) {
              if (!arr || arr.length === 0) {
                return "";
              }
              if (i < arr.length) {
                return arr[i];
              }
              return arr[arr.length - 1];
            }

            function normalizeValue(raw) {
              if (raw === undefined || raw === null) {
                return "";
              }
              if (typeof raw === "number") {
                return String(Math.trunc(raw));
              }
              const text = String(raw).trim();
              if (!text) {
                return "";
              }
              const intMatch = text.match(/^-?\\d+/);
              if (intMatch) {
                return intMatch[0];
              }
              const hexOnly = text.match(/^0x([0-9a-fA-F]+)$/);
              if (hexOnly) {
                return String(parseInt(hexOnly[1], 16));
              }
              return text;
            }

            function extractValueForType(dtypeRaw, cmdObj, cursors, typeCodeToField) {
              const dtypeText = String(dtypeRaw || "");
              const codeMatch = dtypeText.match(/\\((0x[0-9a-fA-F]+)\\)/);
              if (!codeMatch) {
                return "";
              }
              const code = codeMatch[1].toLowerCase();
              const field = typeCodeToField[code];
              if (!field) {
                return "";
              }
              const raw = cmdObj[field];
              if (Array.isArray(raw)) {
                const cursor = cursors[field] || 0;
                const picked = raw.length > 0 ? (cursor < raw.length ? raw[cursor] : raw[raw.length - 1]) : "";
                cursors[field] = cursor + 1;
                return normalizeValue(picked);
              }
              cursors[field] = (cursors[field] || 0) + 1;
              return normalizeValue(raw);
            }

            function hexSort(a, b) {
              return parseInt(a, 16) - parseInt(b, 16);
            }

            const cmd = parseCommand(packet["Command String"]);
            const hasZcl = Object.prototype.hasOwnProperty.call(cmd, "Layer ZBEE_ZCL");
            const isLinkStatus = packet["Packet Type"] === "Link Status (0x08)";

            let zclMsg = null;
            let filteredMsgs = [];
            let currentMsgs = [];
            let voltageMsgs = [];
            let outgoingMsgs = [];
            let thingSpeakMsgs = [];
            let endMsg = null;

            if (hasZcl) {
              const publishTs = Math.floor(Date.now() / 1000);
              const deviceName = String(packet["Device Name ZigBee Source"] || "unknown");

              zclMsg = {
                topic: deviceName,
                payload: {
                  timestamp: publishTs,
                  id: msg.sub_id,
                  "wpan.src": toHex(packet["Source Address"]),
                  "wpan.dst": toHex(packet["Destination Address"]),
                  "zbee.src": toHex(packet["Source Address ZigBee"]),
                  "zbee.dst": toHex(packet["Destination Address ZigBee"]),
                  topic: `ZigBee/${deviceName}`,
                  payload: String(packet["Command String"] || "")
                }
              };

              const attrs = asArray(cmd["Attribute"]);
              const statuses = asArray(cmd["Status"]);
              const dataTypes = asArray(cmd["Data Type"]);
              const sequence = String(cmd["Sequence Number"] || "");

              const typeCodeToField = {
                "0x10": "Boolean",
                "0x18": "Bitmap8",
                "0x19": "Bitmap16",
                "0x1a": "Bitmap24",
                "0x1b": "Bitmap32",
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
                "0x2a": "Int24",
                "0x2b": "Int32",
                "0x2c": "Int40",
                "0x2d": "Int48",
                "0x2e": "Int56",
                "0x2f": "Int64",
                "0x30": "Enum8",
                "0x31": "Enum16"
              };

              const targetNames = {
                "active power": "Active Power",
                "rms current": "RMS Current",
                "rms voltage": "RMS Voltage"
              };

              const valueCursors = {};
              let filteredNo = flow.get("filteredNo") || 0;

              for (let i = 0; i < attrs.length; i += 1) {
                const attrName = cleanLabel(attrs[i]);
                const targetLabel = targetNames[attrName.toLowerCase()];

                const dtypeRaw = pickByIndex(dataTypes, i);
                const statusRaw = pickByIndex(statuses, i);
                const dtypeClean = cleanLabel(dtypeRaw);
                const statusClean = cleanLabel(statusRaw);
                const dataValue = extractValueForType(dtypeRaw, cmd, valueCursors, typeCodeToField);

                if (targetLabel && dtypeClean && dataValue !== "") {
                  filteredNo += 1;
                  filteredMsgs.push({
                    payload: `${filteredNo},${publishTs},${sequence},${targetLabel},${statusClean},${dtypeClean},${dataValue}\\n`
                  });

                  const numMatch = String(dataValue).match(/-?\\d+/);
                  if (numMatch) {
                    const n = Number(numMatch[0]);
                    if (targetLabel === "RMS Current") {
                      currentMsgs.push({ payload: n, topic: "RMS Current" });
                    } else if (targetLabel === "RMS Voltage") {
                      voltageMsgs.push({ payload: n, topic: "RMS Voltage" });
                    }
                  }
                }
              }

              flow.set("filteredNo", filteredNo);
            }

            if (isLinkStatus) {
              const outgoing = flow.get("outgoingCostMap") || {};
              const src = toHex(packet["Source Address ZigBee"]);
              if (src) {
                if (!outgoing[src]) {
                  outgoing[src] = {};
                }
                const links = Array.isArray(cmd["Links"]) ? cmd["Links"] : [];
                for (const link of links) {
                  if (!link || typeof link !== "object") {
                    continue;
                  }
                  const dst = toHex(link["Address"]);
                  if (!dst) {
                    continue;
                  }
                  outgoing[src][dst] = String(link["Outgoing Cost"] ?? "").trim();
                }
              }
              flow.set("outgoingCostMap", outgoing);
            }

            if (msg.sub_count === 200) {
              const outgoing = flow.get("outgoingCostMap") || {};
              const sources = Object.keys(outgoing).sort(hexSort);

              let lineNo = 0;
              for (const src of sources) {
                const destinations = Object.keys(outgoing[src]).sort(hexSort);
                for (const dst of destinations) {
                  lineNo += 1;
                  outgoingMsgs.push({
                    payload: `${lineNo},${src},${dst},${outgoing[src][dst]}\\n`
                  });
                }
              }

              if (sources.length > 0) {
                const smallest = sources[0];
                const destinations = Object.keys(outgoing[smallest]).sort(hexSort);
                for (let i = 0; i < destinations.length; i += 1) {
                  const dst = destinations[i];
                  thingSpeakMsgs.push({
                    payload: {
                      source: smallest,
                      destination: dst,
                      cost: String(outgoing[smallest][dst]),
                      order: i + 1
                    }
                  });
                }
              }

              endMsg = {
                payload: `Stopped at 200 IDs. outgoing_cost rows: ${lineNo}. ThingSpeak queue: ${thingSpeakMsgs.length}.`
              };
            }

            return [
              zclMsg,
              filteredMsgs.length > 0 ? filteredMsgs : null,
              currentMsgs.length > 0 ? currentMsgs : null,
              voltageMsgs.length > 0 ? voltageMsgs : null,
              outgoingMsgs.length > 0 ? outgoingMsgs : null,
              thingSpeakMsgs.length > 0 ? thingSpeakMsgs : null,
              endMsg
            ];
            """
        ),
        "outputs": 7,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 690,
        "y": 500,
        "wires": [
            ["c4d5e6f7a8b90159"],
            ["c5d6e7f8a9b00169"],
            ["c6d7e8f9a0b10279"],
            ["c7d8e9f0a1b20389"],
            ["c8d9e0f1a2b30499"],
            ["c9d0e1f2a3b405a9"],
            ["cad1e2f3a4b506b9"],
        ],
    },
    {
        "id": "c4d5e6f7a8b90159",
        "type": "delay",
        "z": FLOW_ID,
        "name": "Rate limit 10/min",
        "pauseType": "rate",
        "timeout": "5",
        "timeoutUnits": "seconds",
        "rate": "10",
        "nbRateUnits": "1",
        "rateUnits": "minute",
        "randomFirst": "1",
        "randomLast": "5",
        "randomUnits": "seconds",
        "drop": False,
        "allowrate": False,
        "outputs": 1,
        "x": 930,
        "y": 440,
        "wires": [["cb1e2f3a4b5c06c9"]],
    },
    {
        "id": "cb1e2f3a4b5c06c9",
        "type": "json",
        "z": FLOW_ID,
        "name": "Object -> JSON string",
        "property": "payload",
        "action": "",
        "pretty": False,
        "x": 1160,
        "y": 440,
        "wires": [["cc1f2a3b4c5d07d9"]],
    },
    {
        "id": "cc1f2a3b4c5d07d9",
        "type": "mqtt out",
        "z": FLOW_ID,
        "name": "Publish ZCL payload",
        "topic": "",
        "qos": "0",
        "retain": "",
        "respTopic": "",
        "contentType": "",
        "userProps": "",
        "correl": "",
        "expiry": "",
        "broker": BROKER_ID,
        "x": 1370,
        "y": 440,
        "wires": [],
    },
    {
        "id": "c5d6e7f8a9b00169",
        "type": "file",
        "z": FLOW_ID,
        "name": "Append filtered_elems.csv",
        "filename": FILTERED_PATH,
        "filenameType": "str",
        "appendNewline": False,
        "createDir": False,
        "overwriteFile": "false",
        "encoding": "none",
        "x": 980,
        "y": 500,
        "wires": [[]],
    },
    {
        "id": "c6d7e8f9a0b10279",
        "type": "ui_chart",
        "z": FLOW_ID,
        "name": "RMS Current chart",
        "group": UI_GROUP_ID,
        "order": 1,
        "width": 12,
        "height": 6,
        "label": "RMS Current",
        "chartType": "line",
        "legend": "false",
        "xformat": "HH:mm:ss",
        "interpolate": "linear",
        "nodata": "",
        "dot": False,
        "ymin": "",
        "ymax": "",
        "removeOlder": "1",
        "removeOlderPoints": "",
        "removeOlderUnit": "3600",
        "cutout": 0,
        "useOneColor": False,
        "useUTC": False,
        "colors": ["#1f77b4", "#aec7e8", "#ff7f0e"],
        "outputs": 0,
        "useDifferentColor": False,
        "className": "",
        "x": 960,
        "y": 560,
        "wires": [[]],
    },
    {
        "id": "c7d8e9f0a1b20389",
        "type": "ui_chart",
        "z": FLOW_ID,
        "name": "RMS Voltage chart",
        "group": UI_GROUP_ID,
        "order": 2,
        "width": 12,
        "height": 6,
        "label": "RMS Voltage",
        "chartType": "line",
        "legend": "false",
        "xformat": "HH:mm:ss",
        "interpolate": "linear",
        "nodata": "",
        "dot": False,
        "ymin": "",
        "ymax": "",
        "removeOlder": "1",
        "removeOlderPoints": "",
        "removeOlderUnit": "3600",
        "cutout": 0,
        "useOneColor": False,
        "useUTC": False,
        "colors": ["#d62728", "#ff9896", "#9467bd"],
        "outputs": 0,
        "useDifferentColor": False,
        "className": "",
        "x": 960,
        "y": 620,
        "wires": [[]],
    },
    {
        "id": "c8d9e0f1a2b30499",
        "type": "file",
        "z": FLOW_ID,
        "name": "Write outgoing_cost.csv (final)",
        "filename": OUTGOING_PATH,
        "filenameType": "str",
        "appendNewline": False,
        "createDir": False,
        "overwriteFile": "false",
        "encoding": "none",
        "x": 980,
        "y": 680,
        "wires": [[]],
    },
    {
        "id": "c9d0e1f2a3b405a9",
        "type": "delay",
        "z": FLOW_ID,
        "name": "ThingSpeak pace 1/20s",
        "pauseType": "rate",
        "timeout": "5",
        "timeoutUnits": "seconds",
        "rate": "1",
        "nbRateUnits": "20",
        "rateUnits": "second",
        "randomFirst": "1",
        "randomLast": "5",
        "randomUnits": "seconds",
        "drop": False,
        "allowrate": False,
        "outputs": 1,
        "x": 950,
        "y": 740,
        "wires": [["cd102a3b4c5d08e9"]],
    },
    {
        "id": "cd102a3b4c5d08e9",
        "type": "function",
        "z": FLOW_ID,
        "name": "Build ThingSpeak HTTP",
        "func": fn(
            """
            const apiKey = flow.get("thingspeak_write_api_key") || env.get("THINGSPEAK_WRITE_API_KEY");
            if (!apiKey) {
              node.warn("ThingSpeak key missing. Set flow.thingspeak_write_api_key or THINGSPEAK_WRITE_API_KEY.");
              return null;
            }

            const cost = msg.payload && msg.payload.cost !== undefined ? msg.payload.cost : "";
            msg.method = "GET";
            msg.url = `https://api.thingspeak.com/update?api_key=${encodeURIComponent(apiKey)}&field1=${encodeURIComponent(cost)}`;
            msg.payload = "";
            return msg;
            """
        ),
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 1180,
        "y": 740,
        "wires": [["ce203a4b5c6d09f9"]],
    },
    {
        "id": "ce203a4b5c6d09f9",
        "type": "http request",
        "z": FLOW_ID,
        "name": "ThingSpeak update",
        "method": "use",
        "ret": "txt",
        "paytoqs": "ignore",
        "url": "",
        "tls": "",
        "persist": False,
        "proxy": "",
        "insecureHTTPParser": False,
        "authType": "",
        "senderr": False,
        "headers": [],
        "x": 1390,
        "y": 740,
        "wires": [["cf304a5b6c7d10a9"]],
    },
    {
        "id": "cf304a5b6c7d10a9",
        "type": "debug",
        "z": FLOW_ID,
        "name": "ThingSpeak response",
        "active": True,
        "tosidebar": True,
        "console": True,
        "tostatus": False,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 1620,
        "y": 740,
        "wires": [],
    },
    {
        "id": "cad1e2f3a4b506b9",
        "type": "debug",
        "z": FLOW_ID,
        "name": "Execution end",
        "active": True,
        "tosidebar": True,
        "console": False,
        "tostatus": True,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "payload",
        "statusType": "msg",
        "x": 940,
        "y": 800,
        "wires": [],
    },
    {
        "id": BROKER_ID,
        "type": "mqtt-broker",
        "name": "Local Mosquitto (Docker)",
        "broker": MQTT_BROKER_HOST,
        "port": MQTT_BROKER_PORT,
        "clientid": "",
        "autoConnect": True,
        "usetls": False,
        "protocolVersion": "4",
        "keepalive": "60",
        "cleansession": True,
        "autoUnsubscribe": True,
        "birthTopic": "",
        "birthQos": "0",
        "birthRetain": "false",
        "birthPayload": "",
        "birthMsg": {},
        "closeTopic": "",
        "closeQos": "0",
        "closeRetain": "false",
        "closePayload": "",
        "closeMsg": {},
        "willTopic": "",
        "willQos": "0",
        "willRetain": "false",
        "willPayload": "",
        "willMsg": {},
        "userProps": "",
        "sessionExpiry": "",
    },
    {
        "id": UI_TAB_ID,
        "type": "ui_tab",
        "name": "Challenge3",
        "icon": "dashboard",
        "disabled": False,
        "hidden": False,
    },
    {
        "id": UI_GROUP_ID,
        "type": "ui_group",
        "name": "RMS Charts",
        "tab": UI_TAB_ID,
        "order": 1,
        "disp": True,
        "width": "24",
        "collapse": False,
        "className": "",
    },
]

output_path = Path(__file__).resolve().parent / "nodered.txt"
output_path.write_text(json.dumps(nodes, indent=2), encoding="utf-8")
print(f"Wrote {output_path}")
