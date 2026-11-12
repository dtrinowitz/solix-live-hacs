"""Live, read-only aggregated SOLIX sensors."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

LABELS = {
    "solarleistung": "Solarleistung", "ausgangsleistung": "Ausgangsleistung", "hausverbrauch": "Hausverbrauch",
    "hauseinspeisung": "Hauseinspeisung", "ladestand": "Ladestand", "betriebszustand": "Betriebszustand",
}

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SolixValue(hass, entry, key) for key in LABELS])

class SolixValue(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    def __init__(self, hass, entry, key):
        self.hass, self.entry, self.key = hass, entry, key
        self._attr_unique_id = f"solix_live_{key}"
        self._attr_name = LABELS[key]
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, "dashboard")}, name="SOLIX Live", manufacturer="SOLIX Live")
        if key not in ("betriebszustand", "ladestand"):
            self._attr_native_unit_of_measurement = "W"
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif key == "ladestand":
            self._attr_native_unit_of_measurement = "%"
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_track_state_change_event(self.hass, list(self._ids()), self._update)) if self._ids() else None

    def _config(self):
        return {**self.entry.data, **self.entry.options}

    def _ids(self):
        d=self._config(); return {x for k,v in d.items() if k in ("pv_1","pv_2","output_1","output_2","soc_1","soc_2","status_1","status_2","plugs") for x in (v if isinstance(v,list) else [v]) if x}

    @callback
    def _update(self, event):
        self.async_write_ha_state()

    def _value(self, key):
        entity_id=self._config().get(key)
        if not entity_id:return None
        state=self.hass.states.get(entity_id)
        if not state or state.state in ("unknown","unavailable", "none", ""):
            return None
        try:
            value=float(state.state)
            unit=state.attributes.get("unit_of_measurement", "")
            if unit == "kW":value *= 1000
            return max(0.0,value)
        except (TypeError,ValueError):return None

    def _sum(self, keys):
        ids=[key for key in keys if self._config().get(key)]
        if not ids:return None
        values=[self._value(key) for key in ids]
        return None if any(v is None for v in values) else sum(values)

    @property
    def native_value(self):
        if self.key == "solarleistung":return self._sum(["pv_1", "pv_2"])
        if self.key == "ausgangsleistung":return self._sum(["output_1", "output_2"])
        if self.key == "hausverbrauch":
            plugs=self._config().get("plugs", [])
            if not plugs:return None
            values=[]
            for plug in plugs:
                state=self.hass.states.get(plug)
                if state is None or state.state in ("unknown","unavailable"):
                    return None
                try:
                    v=float(state.state)
                    if state.attributes.get("unit_of_measurement")=="kW":v*=1000
                    values.append(max(0,v))
                except (TypeError,ValueError):return None
            return round(sum(values),1)
        if self.key == "hauseinspeisung":
            output=self._sum(["output_1","output_2"])
            plugs=self._plugs_total()
            return None if output is None or plugs is None else max(0,round(output-plugs,1))
        if self.key == "ladestand":
            values=[self._value(k) for k in ("soc_1","soc_2") if self._config().get(k)]
            return None if not values or any(v is None for v in values) else round(sum(values)/len(values),1)
        if self.key == "betriebszustand":
            vals=[]
            for key in ("status_1","status_2"):
                entity_id=self._config().get(key)
                if entity_id:
                    state=self.hass.states.get(entity_id)
                    if state and state.state not in ("unknown","unavailable"):vals.append(state.state)
            return " / ".join(vals) if vals else None

    def _plugs_total(self):
        plugs=self._config().get("plugs",[])
        if not plugs:return None
        total=0
        for plug in plugs:
            state=self.hass.states.get(plug)
            if not state:return None
            try:
                n=float(state.state)
                if state.attributes.get("unit_of_measurement")=="kW":n*=1000
                total+=max(0,n)
            except (TypeError,ValueError):return None
        return total
