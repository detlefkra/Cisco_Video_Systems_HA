import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, AVAILABLE_SENSORS

class CiscoVideoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Ersteinrichtung über die UI."""
    VERSION = 1

    async def _test_credentials(self, host, username, password):
        """Test-Funktion für die Credentials."""
        return True

    async def async_step_user(self, user_input=None):
        """Erster Schritt bei der Einrichtung."""
        errors = {}
        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_HOST], user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(title=f"Cisco {user_input[CONF_HOST]}", data=user_input)
            else:
                errors["base"] = "auth_error"

        DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Erstellt den Options Flow Handler."""
        return CiscoVideoOptionsFlowHandler()


class CiscoVideoOptionsFlowHandler(config_entries.OptionsFlow):
    """Erlaubt das Ändern der ausgewählten Sensoren im Nachhinein."""

    async def async_step_init(self, user_input=None):
        """Initiiert den Optionsschritt."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # HINWEIS: self.config_entry wird jetzt automatisch von Home Assistant bereitgestellt.
        # Wir greifen direkt auf die bereits gespeicherten Optionen zu.
        current_sensors = self.config_entry.options.get(
            CONF_SENSORS, list(AVAILABLE_SENSORS.keys())
        )

        OPTIONS_SCHEMA = vol.Schema({
            vol.Required(
                CONF_SENSORS, 
                default=current_sensors
            ): cv.multi_select(AVAILABLE_SENSORS)
        })

        return self.async_show_form(step_id="init", data_schema=OPTIONS_SCHEMA)
