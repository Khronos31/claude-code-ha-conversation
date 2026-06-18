#!/usr/bin/env python3
import json
import os
import urllib.request
from mcp.server.fastmcp import FastMCP

HA_BASE = "http://supervisor/core/api"

mcp = FastMCP("ha")


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


@mcp.tool()
def get_state(entity_id: str = "") -> str:
    """HAエンティティの状態を取得する。entity_idを省略すると全エンティティの一覧（entity_id・state・friendly_name）を返す。"""
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


@mcp.tool()
def call_service(domain: str, service: str, entity_id: str, service_data: str = "{}") -> str:
    """HAのサービスを呼び出す。例: domain=light, service=turn_on, entity_id=light.living"""
    data = json.loads(service_data)
    data["entity_id"] = entity_id
    result = _post(f"/services/{domain}/{service}", data)
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
