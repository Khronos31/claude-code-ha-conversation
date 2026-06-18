import aiohttp
import logging
from homeassistant.components.conversation import (
    ChatLog,
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import intent
from .const import CONF_SERVER_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ClaudeCodeConversationEntity(entry)])


class ClaudeCodeConversationEntity(ConversationEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = None

    @property
    def supported_languages(self) -> list[str]:
        return ["ja", "en"]

    async def _async_handle_message(self, user_input: ConversationInput, chat_log: ChatLog) -> ConversationResult:
        server_url = self._entry.data[CONF_SERVER_URL]
        payload = {
            "text": user_input.text,
            "conversation_id": user_input.conversation_id,
            "language": user_input.language,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/conversation",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            response_text = data["response"]
            conversation_id = data.get("conversation_id", user_input.conversation_id)
        except Exception as e:
            _LOGGER.error("Claude Code server error: %s", e)
            response_text = "サーバーへの接続に失敗しました。"
            conversation_id = user_input.conversation_id

        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(response_text)
        return ConversationResult(response=response, conversation_id=conversation_id)
