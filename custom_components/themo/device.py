from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .climate import ThemoClimate
from .const import DOMAIN
from .light import ThemoLight
from .sensor import ThemoPowerSensor


class ThemoDevice:
    """Representation of a Themo Device with multiple entities."""

    def __init__(self, device, coordinator: DataUpdateCoordinator):
        """Initialize the Themo device with its entities."""
        self.device = device
        self.coordinator = coordinator
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.name,
            manufacturer="Themo",
            model="Smart Thermostat",
        )
        self.climate = ThemoClimate(device, coordinator, self.device_info)
        self.light = ThemoLight(device, coordinator, self.device_info)
        self.power_sensor = ThemoPowerSensor(device, coordinator, self.device_info)
