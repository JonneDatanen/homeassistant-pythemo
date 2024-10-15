import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

POWER_SENSOR_DESCRIPTION = SensorEntityDescription(
    key="power",
    name="Power",
    native_unit_of_measurement=UnitOfPower.KILO_WATT,
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.POWER,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo power sensor platform from a config entry."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    entities = [
        ThemoPowerSensor(
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


class ThemoPowerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Themo Power Sensor."""

    entity_description: SensorEntityDescription = POWER_SENSOR_DESCRIPTION

    def __init__(
        self, device: Any, coordinator: DataUpdateCoordinator, device_info: DeviceInfo
    ) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device.name} {POWER_SENSOR_DESCRIPTION.name}"
        self._attr_unique_id = f"{device.device_id}_{POWER_SENSOR_DESCRIPTION.key}"
        self._attr_device_info = device_info

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._device.power * self._device.max_power * 1e3
