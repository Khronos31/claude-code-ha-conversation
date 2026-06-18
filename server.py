#!/usr/bin/env python3
import json
import os
import subprocess
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

SESSIONS_FILE = Path("/config/GitHub/claude-code-ha-conversation/sessions.json")
MCP_SERVER = Path("/config/GitHub/claude-code-ha-conversation/mcp_server.py")
SESSION_TIMEOUT = 600  # 10分

ALLOWED_TOOLS = "WebSearch,WebFetch,Read,mcp__ha__get_state,mcp__ha__call_service"
MCP_CONFIG = json.dumps({
    "mcpServers": {
        "ha": {
            "command": "python3",
            "args": [str(MCP_SERVER)],
        }
    }
})

DEFAULT_SYSTEM_PROMPT = (
    "あなたはスマートホームアシスタントです。ユーザーの音声コマンドに日本語で応答し、家電の操作や情報提供を行います。\n"
    "家電操作には get_state と call_service ツールを使ってください。\n"
    "天気や最新情報は WebSearch を使ってください。\n"
    "回答は音声で読み上げられるため、マークダウン記法は使わず、簡潔に答えてください。"
)


def load_sessions():
    if SESSIONS_FILE.exists():
        return json.loads(SESSIONS_FILE.read_text())
    return {}


def save_sessions(sessions):
    SESSIONS_FILE.write_text(json.dumps(sessions))


def get_claude_session(sessions, conversation_id):
    entry = sessions.get(conversation_id)
    if not entry:
        return None
    if time.time() - entry.get("last_seen", 0) > SESSION_TIMEOUT:
        return None
    return entry.get("session_id")


def call_claude(text, model, system_prompt, claude_session_id=None):
    cmd = [
        "claude", "-p",
        "--model", model,
        "--output-format", "json",
        "--allowedTools", ALLOWED_TOOLS,
        "--mcp-config", MCP_CONFIG,
        "--permission-mode", "dontAsk",
    ]
    if claude_session_id:
        cmd += ["--resume", claude_session_id]
    else:
        cmd += ["--system-prompt", system_prompt]
    cmd.append(text)

    env = {**os.environ, "PATH": "/config/.tools/bin:/config/.tools/node/bin:/config/.tools/npm-global/bin:/usr/local/bin:/usr/bin:/bin"}
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"rc={result.returncode} stderr={result.stderr!r} stdout={result.stdout!r}")

    data = json.loads(result.stdout)
    return data["result"], data["session_id"]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/conversation":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        text = body.get("text", "")
        conversation_id = body.get("conversation_id") or "default"
        model = body.get("model", "sonnet")
        system_prompt = body.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

        sessions = load_sessions()
        claude_session_id = get_claude_session(sessions, conversation_id)

        try:
            response_text, new_session_id = call_claude(text, model, system_prompt, claude_session_id)
            sessions[conversation_id] = {
                "session_id": new_session_id,
                "last_seen": time.time(),
            }
            save_sessions(sessions)
        except Exception as e:
            print(f"[error] {e}")
            sessions.pop(conversation_id, None)
            save_sessions(sessions)
            response_text = "すみません、エラーが発生しました。"

        payload = json.dumps({
            "response": response_text,
            "conversation_id": conversation_id,
        }).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print(f"[server] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8765), Handler)
    print("[server] listening on :8765")
    server.serve_forever()
