"""Config flow for Themo integration."""

import logging

from pythemo.client import ThemoAuthenticationError, ThemoClient, ThemoConnectionError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.httpx_client import get_async_client

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


class ThemoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Themo integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Attempt to authenticate with the provided credentials
                themo_client = ThemoClient(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    client=get_async_client(self.hass),
                )

                await themo_client.authenticate()
                return self.async_create_entry(title="Themo", data=user_input)

            except ThemoAuthenticationError as e:
                _LOGGER.error("Failed to authenticate with Themo: %s", e)
                errors = {"base": "invalid_auth"}
            except ThemoConnectionError as e:
                _LOGGER.error("Failed to connect to Themo: %s", e)
                errors = {"base": "cannot_connect"}
            except Exception as e:  # noqa: BLE001
                _LOGGER.error("An unknown error occurred: %s", e)
                errors = {"base": "unknown"}

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )

    async def async_step_reauth(self, entry_data) -> FlowResult:
        """Handle re-authentication when credentials are rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        """Show re-authentication form and validate new credentials."""
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if entry is None:
            return self.async_abort(reason="entry_not_found")

        if user_input is not None:
            try:
                themo_client = ThemoClient(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    client=get_async_client(self.hass),
                )
                await themo_client.authenticate()
            except ThemoAuthenticationError as e:
                _LOGGER.error("Failed to re-authenticate with Themo: %s", e)
                errors = {"base": "invalid_auth"}
            except ThemoConnectionError as e:
                _LOGGER.error("Failed to connect to Themo during reauth: %s", e)
                errors = {"base": "cannot_connect"}
            except Exception as e:  # noqa: BLE001
                _LOGGER.error("Unknown error during Themo reauth: %s", e)
                errors = {"base": "unknown"}
            else:
                self.hass.config_entries.async_update_entry(entry, data=user_input)
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data.get(CONF_USERNAME, "") if entry else "",
                    ): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
            errors=errors,
        )