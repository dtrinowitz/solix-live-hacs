"""SOLIX Live: derived sensors and dashboard panel."""
from pathlib import Path
from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass, entry):
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not hass.data.get(DOMAIN):
        hass.data[DOMAIN] = True
        await hass.http.async_register_static_paths([
            StaticPathConfig("/solix_live/solix-live-panel.js", str(Path(__file__).parent / "frontend" / "solix-live-panel.js"), cache_headers=False)
        ])
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name="solix-live-panel",
            frontend_url_path="solix-live",
            module_url="/solix_live/solix-live-panel.js",
            sidebar_title="SOLIX Energie",
            sidebar_icon="mdi:solar-power",
            require_admin=False,
        )
    entry.async_on_unload(entry.add_update_listener(_update))
    return True

async def _update(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
