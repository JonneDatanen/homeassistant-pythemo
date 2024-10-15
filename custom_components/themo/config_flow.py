import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from pythemo.client import ThemoClient

from .const import DOMAIN

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
                )

                await themo_client.authenticate()
                return self.async_create_entry(title="Themo", data=user_input)
            except Exception:
                errors["base"] = "auth"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ThemoOptionsFlowHandler(config_entry)


class ThemoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Themo options."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_show_form(step_id="init", data_schema=DATA_SCHEMA_USER)
