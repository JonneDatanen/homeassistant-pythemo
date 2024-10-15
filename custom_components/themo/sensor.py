import logging
from typing import Any, List, Type

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

TEMPERATURE_SENSOR_DESCRIPTION = SensorEntityDescription(
    key="temperature",
    name="Temperature",
    native_unit_of_measurement="°C",
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.TEMPERATURE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Themo sensor platform from a config entry."""
    devices = hass.data[DOMAIN]["devices"]
    coordinator = hass.data[DOMAIN]["coordinator"]
    entities = []

    sensor_classes = [
        ThemoPowerSensor,
        ThemoFloorTemperatureSensor,
        ThemoRoomTemperatureSensor,
    ]

    for device in devices:
        entities.extend(create_sensors(device, coordinator, sensor_classes))

    async_add_entities(entities)


def create_sensors(
    device: Any,
    coordinator: DataUpdateCoordinator,
    sensor_classes: List[Type[SensorEntity]],
) -> List[SensorEntity]:
    """Create sensor entities for a device."""
    device_info = DeviceInfo(
        identifiers={(DOMAIN, device.device_id)},
        name=device.name,
        manufacturer="Themo",
        model="Smart Thermostat",
        sw_version=device.sw_version,
    )
    return [
        sensor_class(device, coordinator, device_info)
        for sensor_class in sensor_classes
    ]


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


class ThemoFloorTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Themo Floor Temperature Sensor."""

    entity_description: SensorEntityDescription = TEMPERATURE_SENSOR_DESCRIPTION

    def __init__(
        self, device: Any, coordinator: DataUpdateCoordinator, device_info: DeviceInfo
    ) -> None:
        """Initialize the floor temperature sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device.name} floor temperature"
        self._attr_unique_id = (
            f"{device.device_id}_floor_{TEMPERATURE_SENSOR_DESCRIPTION.key}"
        )
        self._attr_device_info = device_info

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._device.floor_temperature


class ThemoRoomTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Themo Room Temperature Sensor."""

    entity_description: SensorEntityDescription = TEMPERATURE_SENSOR_DESCRIPTION

    def __init__(
        self, device: Any, coordinator: DataUpdateCoordinator, device_info: DeviceInfo
    ) -> None:
        """Initialize the room temperature sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device.name} room temperature"
        self._attr_unique_id = (
            f"{device.device_id}_room_{TEMPERATURE_SENSOR_DESCRIPTION.key}"
        )
        self._attr_device_info = device_info

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._device.room_temperature
