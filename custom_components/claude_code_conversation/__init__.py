from types import MappingProxyType
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_MODEL, DEFAULT_MODEL, CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT

PLATFORMS = ["conversation"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version == 1:
        opts = dict(entry.options)
        hass.config_entries.async_update_entry(entry, version=2)
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType({
                    CONF_MODEL: opts.get(CONF_MODEL, DEFAULT_MODEL),
                    CONF_SYSTEM_PROMPT: opts.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT),
                }),
                subentry_type="conversation",
                title="Claude Code",
                unique_id=None,
            ),
        )
    return True
