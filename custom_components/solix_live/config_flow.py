"""UI setup for SOLIX Live. No credentials needed."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN

FIELDS = ("pv_1", "pv_2", "output_1", "output_2", "soc_1", "soc_2", "status_1", "status_2", "plugs")

def schema(defaults=None):
    defaults = defaults or {}
    result = {}
    for key in FIELDS:
        label = {"pv_1":"PV-System 1", "pv_2":"PV-System 2", "output_1":"Hausabgabe System 1", "output_2":"Hausabgabe System 2", "soc_1":"Ladestand 1", "soc_2":"Ladestand 2", "status_1":"Betriebszustand 1", "status_2":"Betriebszustand 2", "plugs":"Smart-Plugs"}[key]
        sel = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", multiple=(key=="plugs")))
        result[vol.Optional(key, default=defaults[key]) if key in defaults else vol.Optional(key)] = sel
    return vol.Schema(result)

class SolixLiveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id("solix_live_main")
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="SOLIX Live", data=user_input)
        suggested = {
            "pv_1": "sensor.solarbank_2_e1600_pro_solarleistung",
            "pv_2": "sensor.solarbank_2_e1600_pro_solarleistung_2",
            "output_1": "sensor.solarbank_2_e1600_pro_ac_hausabgabe",
            "output_2": "sensor.solarbank_2_e1600_pro_ac_hausabgabe_2",
            "soc_1": "sensor.solarbank_2_e1600_pro_ladestand",
            "soc_2": "sensor.solarbank_2_e1600_pro_ladestand_2",
            "status_1": "sensor.solarbank_2_e1600_pro_betriebszustand",
            "status_2": "sensor.solarbank_2_e1600_pro_betriebszustand_2",
            "plugs": ["sensor.smart_plug_leistung"],
        }
        detected = {k:v for k,v in suggested.items() if all(self.hass.states.get(entity) is not None for entity in (v if isinstance(v,list) else [v]))}
        return self.async_show_form(step_id="user", data_schema=schema(detected))
    @staticmethod
    def async_get_options_flow(config_entry):
        return SolixLiveOptionsFlow()

class SolixLiveOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=schema({**self.config_entry.data, **self.config_entry.options}))
