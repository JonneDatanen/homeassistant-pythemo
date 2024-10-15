import logging
from typing import Any

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pythemo.models import Device

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo light platform from a config entry."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    entities = [
        ThemoLight(
            device,
            coordinator,
            DeviceInfo(
                identifiers={(DOMAIN, device.device_id)},
                name=device.name,
                manufacturer="Themo",
                model="Smart Thermostat",
            ),
        )
        for device in devices
    ]
    async_add_entities(entities)


class ThemoLight(CoordinatorEntity, LightEntity):
    """Representation of a Themo Light entity."""

    def __init__(
        self,
        device: Device,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = device.name
        self._attr_unique_id = f"{device.device_id}_light"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._device.lights

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        _LOGGER.info("Turning light on for device: %s", self._device)
        await self._device.set_lights(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        _LOGGER.info("Turning light off for device: %s", self._device)
        await self._device.set_lights(False)
        self.async_write_ha_state()
