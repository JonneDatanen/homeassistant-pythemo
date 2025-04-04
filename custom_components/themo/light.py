"""Module containing the Themo light platform integration for Home Assistant."""

import logging
from typing import Any

from pythemo.models import Device

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .helpers import async_setup_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo light platform from a config entry."""
    await async_setup_device(hass, entry, async_add_entities, [ThemoLight])


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
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
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
