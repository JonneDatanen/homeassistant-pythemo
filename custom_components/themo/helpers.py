"""Module containing helper functions for setting up Themo devices."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    entity_classes: list[Any],
) -> None:
    """Set up Themo device and add entities."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    entities = [
        entity_class(
            device,
            coordinator,
            DeviceInfo(
                identifiers={(DOMAIN, device.device_id)},
                name=device.name,
                manufacturer="Themo",
                model="Smart Thermostat",
                sw_version=device.sw_version,
            ),
        )
        for device in devices
        for entity_class in entity_classes
    ]

    async_add_entities(entities)
