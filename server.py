#!/usr/bin/env python3
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

SESSIONS_FILE = Path("/config/GitHub/claude-code-ha-conversation/sessions.json")
ALLOWED_TOOLS = "WebSearch,WebFetch,Bash(ha-get-state *),Bash(ha-call-service *),Read"

SYSTEM_PROMPT = """\
あなたはスマートホームアシスタントです。ユーザーの音声コマンドに日本語で応答し、家電の操作や情報提供を行います。

家電操作には ha-get-state と ha-call-service ツールを使ってください。
天気や最新情報は WebSearch を使ってください。

回答は音声で読み上げられるため、マークダウン記法は使わず、簡潔に答えてください。\
"""


def load_sessions():
    if SESSIONS_FILE.exists():
        return json.loads(SESSIONS_FILE.read_text())
    return {}


def save_sessions(sessions):
    SESSIONS_FILE.write_text(json.dumps(sessions))


def call_claude(text, claude_session_id=None):
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--allowedTools", ALLOWED_TOOLS,
        "--permission-mode", "dontAsk",
    ]
    if claude_session_id:
        cmd += ["--resume", claude_session_id]
    else:
        cmd += ["--system-prompt", SYSTEM_PROMPT]
    cmd.append(text)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

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

        sessions = load_sessions()
        claude_session_id = sessions.get(conversation_id)

        try:
            response_text, new_session_id = call_claude(text, claude_session_id)
            sessions[conversation_id] = new_session_id
            save_sessions(sessions)
        except Exception as e:
            print(f"[error] {e}")
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
