import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector, SelectSelectorConfig, SelectSelectorMode,
    TemplateSelector,
)
from .const import (
    DOMAIN,
    CONF_SERVER_URL, DEFAULT_SERVER_URL,
    CONF_MODEL, DEFAULT_MODEL,
    CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT,
)

MODELS = ["haiku", "sonnet", "opus"]

MODEL_SELECTOR = SelectSelector(SelectSelectorConfig(options=MODELS, mode=SelectSelectorMode.DROPDOWN))
PROMPT_SELECTOR = TemplateSelector()


def _subentry_schema(defaults):
    return vol.Schema({
        vol.Optional(CONF_MODEL, default=defaults.get(CONF_MODEL, DEFAULT_MODEL)): MODEL_SELECTOR,
        vol.Optional(CONF_SYSTEM_PROMPT, default=defaults.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT)): PROMPT_SELECTOR,
    })


class ClaudeCodeConversationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
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

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry):
        return {"conversation": ClaudeCodeSubentryFlowHandler}


class ClaudeCodeSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Claude Code", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_subentry_schema({}),
        )

    async def async_step_reconfigure(self, user_input=None):
        subentry = self._get_reconfigure_subentry()

        if user_input is not None:
            return self.async_update_and_abort(
                self._get_entry(),
                subentry,
                data=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_subentry_schema(dict(subentry.data)),
        )
