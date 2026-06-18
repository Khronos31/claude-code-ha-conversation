import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_SERVER_URL, DEFAULT_SERVER_URL


class ClaudeCodeConversationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Claude Code Conversation",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SERVER_URL, default=DEFAULT_SERVER_URL): str,
            }),
        )
