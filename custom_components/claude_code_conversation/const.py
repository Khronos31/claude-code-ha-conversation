DOMAIN = "claude_code_conversation"
CONF_SERVER_URL = "server_url"
DEFAULT_SERVER_URL = "http://localhost:8765"

CONF_MODEL = "model"
CONF_SYSTEM_PROMPT = "system_prompt"
DEFAULT_MODEL = "sonnet"
DEFAULT_SYSTEM_PROMPT = (
    "あなたはスマートホームアシスタントです。ユーザーの音声コマンドに日本語で応答し、家電の操作や情報提供を行います。\n"
    "家電操作には ha-get-state と ha-call-service ツールを使ってください。\n"
    "天気や最新情報は WebSearch を使ってください。\n"
    "回答は音声で読み上げられるため、マークダウン記法は使わず、簡潔に答えてください。"
)
