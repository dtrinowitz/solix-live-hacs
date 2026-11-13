"""Live, read-only aggregated SOLIX sensors."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
import math
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from .mirror import SolixMirrorManager, discover_sources

LABELS = {
    "solarleistung": "Solarleistung", "ausgangsleistung": "Ausgangsleistung", "hausverbrauch": "Hausverbrauch",
    "hauseinspeisung": "Hauseinspeisung", "ladestand": "Ladestand", "betriebszustand": "Betriebszustand",
    "systemdetails": "Systemdetails",
}

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SolixValue(hass, entry, key) for key in LABELS])
    manager = SolixMirrorManager(hass, async_add_entities)
    manager.refresh()
    # Registry changes can add newly discovered devices and entities at runtime.
    from homeassistant.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED
    entry.async_on_unload(hass.bus.async_listen(EVENT_ENTITY_REGISTRY_UPDATED, manager.refresh))
    from homeassistant.helpers.device_registry import EVENT_DEVICE_REGISTRY_UPDATED
    entry.async_on_unload(hass.bus.async_listen(EVENT_DEVICE_REGISTRY_UPDATED, manager.refresh))

class SolixValue(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    def __init__(self, hass, entry, key):
        self.hass, self.entry, self.key = hass, entry, key
        self._attr_unique_id = f"solix_live_{key}"
        self._attr_name = LABELS[key]
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, "dashboard")}, name="SOLIX Live", manufacturer="SOLIX Live")
        if key not in ("betriebszustand", "ladestand", "systemdetails"):
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
        if self.key == "systemdetails":
            self._source_ids = set(discover_sources(self.hass))
            self.async_on_remove(self.hass.bus.async_listen("state_changed", self._detail_changed))
            self.async_on_remove(self.hass.bus.async_listen("entity_registry_updated", self._detail_registry_changed))


    def _config(self):
        return {**self.entry.data, **self.entry.options}

    def _ids(self):
        d=self._config(); return {x for k,v in d.items() for x in (v if isinstance(v,list) else [v]) if isinstance(x,str) and x}

    @callback
    def _detail_changed(self, event):
        if event.data.get("entity_id") in self._source_ids:
            self.async_write_ha_state()

    @callback
    def _detail_registry_changed(self, event):
        self._source_ids = set(discover_sources(self.hass))
        self.async_write_ha_state()

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
            return max(0.0,value) if math.isfinite(value) else None
        except (TypeError,ValueError):return None

    def _sum(self, keys):
        ids=[key for key in keys if self._config().get(key)]
        if not ids:return None
        values=[self._value(key) for key in ids]
        available = [v for v in values if v is not None]
        return round(sum(available), 1) if available else None

    def _plug_readings(self):
        """Read each plug independently; never let one broken plug block the others."""
        plugs = self._config().get("plugs", []) or []
        if isinstance(plugs, str):
            plugs = [plugs]
        total = 0.0
        valid, missing = [], []
        for plug in plugs:
            state = self.hass.states.get(plug)
            try:
                if state is None or state.state.lower() in ("unknown", "unavailable", "none", ""):
                    raise ValueError("not available")
                value = float(state.state)
                if not math.isfinite(value):
                    raise ValueError("not finite")
                unit = state.attributes.get("unit_of_measurement", "W")
                if unit == "kW":
                    value *= 1000
                elif unit != "W":
                    raise ValueError("not a power sensor")
                total += max(0.0, value)
                valid.append(plug)
            except (ValueError, TypeError, AttributeError):
                missing.append(plug)
        return round(total, 1) if valid else None, valid, missing, len(plugs)

    @property
    def extra_state_attributes(self):
        if self.key == "systemdetails":
            return self._system_details()
        if self.key not in ("hausverbrauch", "hauseinspeisung", "solarleistung", "ausgangsleistung"):
            return None
        if self.key in ("solarleistung", "ausgangsleistung"):
            keys = ("pv_1", "pv_2") if self.key == "solarleistung" else ("output_1", "output_2")
            selected = [key for key in keys if self._config().get(key)]
            missing = [key for key in selected if self._value(key) is None]
            return {"sources_configured": len(selected), "sources_available": len(selected) - len(missing), "sources_unavailable": missing, "incomplete": bool(missing)}
        _, valid, missing, count = self._plug_readings()
        return {
            "smart_plugs_configured": count,
            "smart_plugs_available": len(valid),
            "smart_plugs_unavailable": missing,
            "incomplete": bool(missing),
            "value_quality": "partial" if missing and valid else ("unavailable" if not valid else "complete"),
        }

    def _system_details(self):
        """Discover live device values using actual HA device associations.

        Never assign a reading to an arbitrary system number. Manual selections
        take precedence, while automatic readings are grouped by original device.
        """
        config = self._config()
        sources = discover_sources(self.hass)
        grouped = {}
        for entity_id, (record, device) in sources.items():
            device_key = device.id if device else "unassigned"
            label = ((getattr(device, "name_by_user", None) or getattr(device, "name", None))
                     if device else "Weitere Anker-SOLIX-Entitäten")
            grouped.setdefault(device_key, {"name": label, "readings": []})["readings"].append(
                (entity_id, (record.name or record.original_name or entity_id).lower()))

        def reading(entity_id):
            state = self.hass.states.get(entity_id) if entity_id else None
            if not state or state.state.lower() in ("unknown", "unavailable", "none", ""):
                return None
            try:
                value = float(state.state)
                if not math.isfinite(value):
                    return None
                if state.attributes.get("unit_of_measurement") == "kW":
                    value *= 1000
                return value
            except (TypeError, ValueError):
                return None

        def select_metric(items, metric):
            terms = {
                "temp": ("temperatur", "temperature", "battery_temp", "bat_temp"),
                "soc": ("ladestand", "battery_soc", "state_of_charge", "akku_soc", "battery_level", "capacity"),
                "power": ("ladeleistung", "entladeleistung", "battery_power", "bat_power", "charging_power", "discharging_power"),
            }[metric]
            candidates = []
            for entity_id, label in items:
                name = entity_id.split(".", 1)[-1].lower() + " " + label
                if any(term in name for term in terms):
                    state = self.hass.states.get(entity_id)
                    unit = state.attributes.get("unit_of_measurement") if state else None
                    expected = {"temp": ("°C", "°F"), "soc": ("%",), "power": ("W", "kW")}[metric]
                    if unit in expected:
                        candidates.append(entity_id)
            # Ambiguous matches must not be silently attributed to a device.
            return reading(candidates[0]) if len(candidates) == 1 else None

        devices = []
        for group in grouped.values():
            items = group["readings"]
            devices.append({"name": group["name"], "heated": True,
                            "temp": select_metric(items, "temp"),
                            "soc": select_metric(items, "soc"),
                            "power": select_metric(items, "power"),
                            "source_count": len(items)})

        # Preserve manual per-device readings when present, but do not label
        # an unknown device as a specific Solarbank based on ordering.
        manually_configured = []
        for key in ("pro_1", "pro_2", "e1600_1", "e1600_2"):
            if any(config.get(f"{key}_{metric}") for metric in ("temp", "soc", "power")):
                manually_configured.append({
                    "name": "Manuell zugeordnet · " + key,
                    "temp": reading(config.get(f"{key}_temp")),
                    "soc": reading(config.get(f"{key}_soc")),
                    "power": reading(config.get(f"{key}_power")),
                })
        devices.extend(manually_configured)

        mppts = []
        for system in (1, 2):
            for index in range(1, 5):
                entity_id = config.get(f"pro_{system}_mppt_{index}")
                if entity_id:
                    mppts.append({"system": system, "index": index,
                                  "power": reading(entity_id)})
        plugs = config.get("plugs", []) or []
        if isinstance(plugs, str):
            plugs = [plugs]
        plug_values = []
        for entity_id in plugs:
            state = self.hass.states.get(entity_id)
            plug_values.append({"name": state.attributes.get("friendly_name", entity_id)
                                if state else entity_id, "power": reading(entity_id)})
        return {"devices": devices, "mppts": mppts, "plugs": plug_values,
                "discovered_source_entities": len(sources)}

    @property
    def native_value(self):
        if self.key == "systemdetails":
            return "Bereit"
        if self.key == "solarleistung":
            return self._sum(["pv_1", "pv_2"])
        if self.key == "ausgangsleistung":
            return self._sum(["output_1", "output_2"])
        if self.key == "hausverbrauch":
            total, _, _, _ = self._plug_readings()
            return total
        if self.key == "hauseinspeisung":
            output = self._sum(["output_1", "output_2"])
            plugs, _, _, _ = self._plug_readings()
            return None if output is None or plugs is None else max(0, round(output - plugs, 1))
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
