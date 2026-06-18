#!/usr/bin/env python3
"""Minimal MCP stdio server using only stdlib — no mcp package dependency."""
import json
import os
import sys
import urllib.request

HA_BASE = "http://supervisor/core/api"

TOOLS = [
    {
        "name": "get_state",
        "description": "HAエンティティの状態を取得する。entity_idを省略すると全エンティティの一覧（entity_id・state・friendly_name）を返す。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "エンティティID（省略可）"}
            },
        },
    },
    {
        "name": "call_service",
        "description": "HAのサービスを呼び出す。例: domain=light, service=turn_on, entity_id=light.living",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "service": {"type": "string"},
                "entity_id": {"type": "string"},
                "service_data": {"type": "string", "description": "追加パラメータのJSON文字列"},
            },
            "required": ["domain", "service", "entity_id"],
        },
    },
]


def _headers():
    return {
        "Authorization": f"Bearer {os.environ['SUPERVISOR_TOKEN']}",
        "Content-Type": "application/json",
    }


def _get(path):
    req = urllib.request.Request(f"{HA_BASE}{path}", headers=_headers())
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _post(path, data=None):
    body = json.dumps(data or {}).encode()
    req = urllib.request.Request(f"{HA_BASE}{path}", data=body, headers=_headers(), method="POST")
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        return json.loads(content) if content else {}


def tool_get_state(args):
    entity_id = args.get("entity_id", "")
    if entity_id:
        return json.dumps(_get(f"/states/{entity_id}"), ensure_ascii=False)
    states = _get("/states")
    compact = [
        {
            "entity_id": s["entity_id"],
            "state": s["state"],
            "friendly_name": s.get("attributes", {}).get("friendly_name", ""),
        }
        for s in states
    ]
    return json.dumps(compact, ensure_ascii=False)


def tool_call_service(args):
    data = json.loads(args.get("service_data", "{}"))
    data["entity_id"] = args["entity_id"]
    result = _post(f"/services/{args['domain']}/{args['service']}", data)
    return json.dumps(result, ensure_ascii=False)


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def handle(msg):
    method = msg.get("method", "")
    msg_id = msg.get("id")

    if method == "initialize":
        send({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ha", "version": "1.0"},
            },
        })
    elif method in ("notifications/initialized", "notifications/cancelled"):
        pass
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "get_state":
                text = tool_get_state(args)
            elif name == "call_service":
                text = tool_call_service(args)
            else:
                raise ValueError(f"Unknown tool: {name}")
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": text}], "isError": False},
            })
        except Exception as e:
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": str(e)}], "isError": True},
            })
    elif msg_id is not None:
        send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}})


if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except json.JSONDecodeError:
            pass
