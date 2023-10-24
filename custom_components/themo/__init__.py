import logging
from datetime import timedelta
from typing import Any

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pythemo.client import ThemoClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "themo"
SCAN_INTERVAL = timedelta(minutes=2)


async def async_setup(hass: Any, config: dict[str, Any]) -> bool:
    """Set up the Themo component."""
    username = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]

    client = ThemoClient(username, password)
    await client.authenticate()
    devices = await client.get_all_devices()

    async def async_update_data() -> list:
        """Fetch data from API endpoint."""
        for device in devices:
            await device.update_state()
        return devices

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="themo_device_update",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()
    hass.data[DOMAIN] = {"devices": devices, "coordinator": coordinator}
    hass.helpers.discovery.load_platform("light", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("climate", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    return True
