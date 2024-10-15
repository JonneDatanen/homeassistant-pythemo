import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pythemo.models import Device

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

THEMO_TO_HA_MODES = {
    "Off": HVAC_MODE_OFF,
    "Manual": HVAC_MODE_HEAT,
    "SLS": HVAC_MODE_AUTO,
}
HA_TO_THEMO_MODES = {v: k for k, v in THEMO_TO_HA_MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo climate platform from a config entry."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    entities = []
    for device in devices:
        device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.name,
            manufacturer="Themo",
            model="Smart Thermostat",
        )
        entities.append(ThemoClimate(device, coordinator, device_info))
    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        "set_active_schedule",
        {vol.Required("schedule_name"): cv.string},
        "set_active_schedule",
    )


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
    def supported_features(self) -> int:
        """Return supported features."""
        if self.hvac_mode == HVAC_MODE_AUTO:
            return SUPPORT_PRESET_MODE
        elif self.hvac_mode == HVAC_MODE_HEAT:
            return SUPPORT_TARGET_TEMPERATURE
        else:
            return 0

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._device.info

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        return self._device.manual_temperature

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode."""
        return THEMO_TO_HA_MODES.get(self._device.mode, HVAC_MODE_OFF)

    @property
    def preset_mode(self) -> Optional[str]:
        """Return extra state attributes."""
        return self._device.active_schedule

    @property
    def preset_modes(self) -> Optional[list]:
        """Return extra state attributes."""
        return self._device.available_schedules

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature and self.hvac_mode == HVAC_MODE_HEAT:
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
