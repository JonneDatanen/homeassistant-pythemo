"""Module containing the Themo climate platform integration for Home Assistant."""

import logging
from typing import Any

from pythemo.models import Device

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
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

# Manual temperature range accepted by the Themo API (CMT command).
MIN_TEMPERATURE = 13.0
MAX_TEMPERATURE = 41.0
TEMPERATURE_STEP = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo climate platform from a config entry."""
    await async_setup_device(hass, entry, async_add_entities, [ThemoClimate])


class ThemoClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Themo Climate entity."""

    # The climate entity is the main feature of the device, so it carries the
    # device name itself; the other entities get a suffix.
    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMPERATURE
    _attr_max_temp = MAX_TEMPERATURE
    _attr_target_temperature_step = TEMPERATURE_STEP
    # Advertise a fixed feature set so the thermostat card always renders the
    # setpoint control. Changing the setpoint while in Off/Auto switches the
    # device to Manual mode, see async_set_temperature.
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        device: Device,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{device.device_id}_climate"
        self._attr_hvac_modes = list(THEMO_TO_HA_MODES.values())
        self._attr_device_info = device_info

    @property
    def current_temperature(self) -> float | None:
        """Return the temperature of the sensor the device is controlling on."""
        return self._device.info

    @property
    def target_temperature(self) -> float | None:
        """Return the manual target temperature."""
        return self._device.manual_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return THEMO_TO_HA_MODES.get(self._device.mode, HVACMode.OFF)

    @property
    def hvac_action(self) -> HVACAction:
        """Return whether the device is currently heating."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        heating = self._device.load_state
        if heating is None:
            heating = self._device.power
        return HVACAction.HEATING if heating else HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        """Return the active schedule."""
        return self._device.active_schedule

    @property
    def preset_modes(self) -> list | None:
        """Return the available schedules."""
        return self._device.available_schedules

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature.

        The Themo device only follows the manual setpoint in Manual mode, so the
        device is switched to Manual first when it is in Off or Auto (SLS) mode.
        """
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        if hvac_mode is not None and hvac_mode != self.hvac_mode:
            await self.async_set_hvac_mode(hvac_mode)
        elif self.hvac_mode != HVACMode.HEAT:
            await self._device.set_mode(HA_TO_THEMO_MODES[HVACMode.HEAT])

        await self._device.set_manual_temperature(temperature)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        themo_mode = HA_TO_THEMO_MODES.get(hvac_mode)
        if themo_mode:
            await self._device.set_mode(themo_mode)
            self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the active schedule."""
        await self._device.set_active_schedule(preset_mode)
        self.async_write_ha_state()
