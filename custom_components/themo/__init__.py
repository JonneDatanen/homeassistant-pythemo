"""Themo integration for Home Assistant.

This module provides support for Themo devices within Home Assistant.
"""

from datetime import timedelta
import logging

import httpx
from pythemo.client import (
    ThemoAuthenticationError,
    ThemoClient,
    ThemoConnectionError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
DOMAIN = "themo"

SCAN_INTERVAL = timedelta(minutes=2)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Themo component."""
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]

    themo_client = ThemoClient(
        username,
        password,
        client=get_async_client(hass),
    )

    try:
        await themo_client.authenticate()
        devices = await themo_client.get_all_devices()
    except ThemoAuthenticationError as err:
        raise ConfigEntryAuthFailed(
            "Themo authentication failed, please reconfigure credentials"
        ) from err
    except (ThemoConnectionError, httpx.TimeoutException) as err:
        raise ConfigEntryNotReady("Unable to reach Themo API") from err

    async def async_update_data() -> list:
        """Fetch data from API endpoint."""
        for device in devices:
            try:
                await device.update_state()
            except (ThemoConnectionError, httpx.TimeoutException):
                _LOGGER.warning("Timeout while updating device state: %s", device.name)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error updating device state: %s", device.name)
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
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "devices": devices,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.LIGHT, Platform.CLIMATE, Platform.SENSOR]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.LIGHT, Platform.CLIMATE, Platform.SENSOR]
    )
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
