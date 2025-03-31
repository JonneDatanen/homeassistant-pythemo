"""Module containing the Themo climate platform integration for Home Assistant."""

import logging
from typing import Any

from pythemo.models import Device

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .helpers import async_setup_device

_LOGGER = logging.getLogger(__name__)

THEMO_TO_HA_MODES = {
    "Off": HVACMode.OFF,
    "Manual": HVACMode.HEAT,
    "SLS": HVACMode.AUTO,
}
HA_TO_THEMO_MODES = {v: k for k, v in THEMO_TO_HA_MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo climate platform from a config entry."""
    await async_setup_device(hass, entry, async_add_entities, [ThemoClimate])


class ThemoClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Themo Climate entity."""

    def __init__(
        self,
        device: Device,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = device.name
        self._attr_unique_id = f"{device.device_id}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = list(THEMO_TO_HA_MODES.values())
        self._attr_device_info = device_info

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return supported features."""
        if self.hvac_mode == HVACMode.AUTO:
            return (
                ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
            )
        if self.hvac_mode == HVACMode.HEAT:
            return (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
            )

        return ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._device.info

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._device.manual_temperature

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode."""
        return THEMO_TO_HA_MODES.get(self._device.mode, HVACMode.OFF)

    @property
    def preset_mode(self) -> str | None:
        """Return extra state attributes."""
        return self._device.active_schedule

    @property
    def preset_modes(self) -> list | None:
        """Return extra state attributes."""
        return self._device.available_schedules

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature and self.hvac_mode == HVACMode.HEAT:
            await self._device.set_manual_temperature(temperature)
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set the HVAC mode."""
        themo_mode = HA_TO_THEMO_MODES.get(hvac_mode)
        if themo_mode:
            await self._device.set_mode(themo_mode)
            self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the active schedule."""
        await self._device.set_active_schedule(preset_mode)
        self.async_write_ha_state()
