"""Read-only mirrors of SOLIX source entities, discovered from HA's entity registry.

Mirrors are intentionally distinct entities: originals remain the source of truth.
"""
import logging
import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SOURCE_DOMAINS = {"anker_solix", "anker_solix2", "anker_solix_api"}
NAME_PATTERN = re.compile(r"anker|solix|solarbank|e1600|system_sb_", re.I)


def discover_sources(hass):
    """Return entity-registry records with provable SOLIX provenance.

    Device links and integration domain take precedence over names; names are a
    fallback for installations whose third-party integration uses another domain.
    Never mirror our own entities, and never mirror unrelated HA entities.
    """
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    found = {}
    for entity in entities.entities.values():
        if entity.platform == DOMAIN or entity.entity_id.startswith("sensor.solix_live_"):
            continue
        device = devices.async_get(entity.device_id) if entity.device_id else None
        device_label = " ".join(str(x or "") for x in (
            getattr(device, "name_by_user", None), getattr(device, "name", None),
            getattr(device, "manufacturer", None), getattr(device, "model", None),
        )) if device else ""
        is_solix = (entity.platform in SOURCE_DOMAINS
                    or bool(NAME_PATTERN.search(device_label))
                    or bool(NAME_PATTERN.search(entity.entity_id + " " + (entity.original_name or ""))))
        if not is_solix:
            continue
        # Do not copy our own mirror or aggregate entities even if their name matches.
        if entity.config_entry_id:
            config = hass.config_entries.async_get_entry(entity.config_entry_id)
            if config and config.domain == DOMAIN:
                continue
        found[entity.entity_id] = (entity, device)
    return found


class SolixMirror(SensorEntity):
    """A read-only representation of one original HA entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(self, hass, source_id, source_entry, source_device):
        self.hass = hass
        self.source_id = source_id
        source_state = hass.states.get(source_id)
        if source_state:
            unit = source_state.attributes.get("unit_of_measurement")
            try:
                float(source_state.state)
                if unit:
                    self._attr_native_unit_of_measurement = unit
            except (TypeError, ValueError):
                pass
        self._attr_unique_id = f"solix_mirror_{source_id}"
        self._attr_name = (source_entry.name or source_entry.original_name
                           or source_id.split(".", 1)[-1].replace("_", " "))
        original_name = (getattr(source_device, "name_by_user", None)
                         or getattr(source_device, "name", None)
                         or "Anker SOLIX · Sonstige")
        source_identifier = source_device.id if source_device else source_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"mirror_device_{source_identifier}")},
            name=original_name,
            manufacturer="Anker SOLIX · Quelle",
            model=getattr(source_device, "model", None) if source_device else None,
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_track_state_change_event(
            self.hass, [self.source_id], self._source_changed))

    @callback
    def _source_changed(self, event):
        self.async_write_ha_state()

    @property
    def available(self):
        state = self.hass.states.get(self.source_id)
        return state is not None and state.state not in ("unknown", "unavailable")

    @property
    def native_value(self):
        state = self.hass.states.get(self.source_id)
        if not state or not self.available:
            return None
        if self.native_unit_of_measurement:
            try:
                return float(state.state)
            except (TypeError, ValueError):
                return None
        return state.state

    @property
    def extra_state_attributes(self):
        state = self.hass.states.get(self.source_id)
        attrs = {"source_entity_id": self.source_id,
                 "source_domain": self.source_id.split(".", 1)[0],
                 "read_only_mirror": True}
        if state:
            for key in ("unit_of_measurement", "device_class", "state_class"):
                if key in state.attributes:
                    attrs[f"source_{key}"] = state.attributes[key]
        return attrs


class SolixMirrorManager:
    def __init__(self, hass, async_add_entities):
        self.hass = hass
        self.async_add_entities = async_add_entities
        self.registered = set()

    @callback
    def refresh(self, event=None):
        new = []
        for source_id, (source_entry, source_device) in discover_sources(self.hass).items():
            if source_id not in self.registered:
                self.registered.add(source_id)
                new.append(SolixMirror(self.hass, source_id, source_entry, source_device))
        if new:
            _LOGGER.info("SOLIX Live: registering %s additional source mirrors", len(new))
            self.async_add_entities(new)