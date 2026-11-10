"""Dienste für die Cisco Video System Integration."""
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN  # Falls DOMAIN in const.py liegt, sonst "cisco_video_system"

SERVICE_DIAL = "dial"
SERVICE_HANGUP = "hangup"
SERVICE_SET_VOLUME = "set_volume"
SERVICE_MUTE_MICROPHONES = "mute_microphones"
SERVICE_SET_STANDBY = "set_standby"

ATTR_NUMBER = "number"
ATTR_VOLUME = "volume"
ATTR_MUTE = "mute"
ATTR_STANDBY = "standby"

def async_setup_services(hass: HomeAssistant) -> None:
    """Registriere Cisco xAPI Dienste."""

    async def execute_service(call: ServiceCall):
        """Führe den aufgerufenen Dienst aus."""
        # Holt den ersten konfigurierten Eintrag aus hass.data
        entry_ids = list(hass.data[DOMAIN].keys())
        if not entry_ids:
            return
        
        # Passe diesen Pfad an die Struktur deiner __init__.py an
        api = hass.data[DOMAIN][entry_ids[0]]["api"]

        if call.service == SERVICE_DIAL:
            await api.dial(call.data[ATTR_NUMBER])
        elif call.service == SERVICE_HANGUP:
            await api.hangup()
        elif call.service == SERVICE_SET_VOLUME:
            await api.set_volume(call.data[ATTR_VOLUME])
        elif call.service == SERVICE_MUTE_MICROPHONES:
            await api.mute_microphones(call.data[ATTR_MUTE])
        elif call.service == SERVICE_SET_STANDBY:
            await api.set_standby(call.data[ATTR_STANDBY])

    # Dienste registrieren und Schemas validieren
    hass.services.async_register(
        DOMAIN, SERVICE_DIAL, execute_service,
        schema=vol.Schema({vol.Required(ATTR_NUMBER): cv.string})
    )
    hass.services.async_register(DOMAIN, SERVICE_HANGUP, execute_service)
    
    hass.services.async_register(
        DOMAIN, SERVICE_SET_VOLUME, execute_service,
        schema=vol.Schema({vol.Required(ATTR_VOLUME): vol.All(vol.Coerce(int), vol.Range(min=0, max=100))})
    )
    hass.services.async_register(
        DOMAIN, SERVICE_MUTE_MICROPHONES, execute_service,
        schema=vol.Schema({vol.Required(ATTR_MUTE): cv.boolean})
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_STANDBY, execute_service,
        schema=vol.Schema({vol.Required(ATTR_STANDBY): cv.boolean})
    )

