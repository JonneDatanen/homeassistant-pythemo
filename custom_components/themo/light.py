import logging
from typing import Any

from homeassistant.components.light import LightEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pythemo.models import Device

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: Any,
    config: dict,
    add_entities: Any,
    discovery_info: Any = None,
) -> None:
    """Set up the Themo light platform."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    add_entities(ThemoLight(device, coordinator) for device in devices)


class ThemoLight(CoordinatorEntity, LightEntity):
    """Representation of a Themo Light entity."""

    def __init__(self, device: Device, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the light entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = device.name
        self._attr_unique_id = f"{device.device_id}_light"

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
