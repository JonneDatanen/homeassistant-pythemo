import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo power sensor platform from a config entry."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([ThemoPowerSensor(device, coordinator) for device in devices])


POWER_SENSOR_DESCRIPTION = SensorEntityDescription(
    key="power",
    name="Power",
    native_unit_of_measurement=UnitOfPower.KILO_WATT,
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.POWER,
)


class ThemoPowerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Themo Power Sensor."""

    entity_description: SensorEntityDescription = POWER_SENSOR_DESCRIPTION

    def __init__(self, device: Any, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device.name} {POWER_SENSOR_DESCRIPTION.name}"
        self._attr_unique_id = f"{device.device_id}_{POWER_SENSOR_DESCRIPTION.key}"

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._device.power * self._device.max_power * 1e3
