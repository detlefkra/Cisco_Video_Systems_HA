import logging
import xml.etree.ElementTree as ET
import aiohttp
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Cisco Video System Integration aus einem Config Entry auf."""
    hass.data.setdefault(DOMAIN, {})
    
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    # Weiterleitung an die Sensor-Plattformen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Hilfsfunktion zum Senden der XML-Befehle an /putxml
    async def send_xcommand(xml_payload: str):
        session = async_get_clientsession(hass)
        
        # Sicherstellen, dass die URL korrekt formatiert ist
        cleaned_host = host
        if not cleaned_host.startswith(("http://", "https://")):
            cleaned_host = f"https://{cleaned_host}"
        url = f"{cleaned_host.rstrip('/')}/putxml"
        
        auth = aiohttp.BasicAuth(username, password)
        headers = {"Content-Type": "text/xml"}
        
        try:
            async with session.post(url, data=xml_payload, auth=auth, headers=headers, ssl=False) as response:
                if response.status == 200:
                    text = await response.text()
                    _LOGGER.debug("Cisco API Antwort: %s", text)
                else:
                    _LOGGER.error("Fehler beim Senden an Cisco API. Status: %s", response.status)
        except Exception as err:
            _LOGGER.error("Verbindungsfehler zur Cisco API: %s", err)

    # Dienst-Handler für die xAPI Steuerbefehle
    async def handle_cisco_service(call: ServiceCall):
        service = call.service
        
        if service == "dial":
            target = call.data.get("target")
            payload = f"<Command><Dial><Number>{target}</Number></Dial></Command>"
            await send_xcommand(payload)
            
        elif service == "disconnect":
            payload = "<Command><Call><Disconnect/></Call></Command>"
            await send_xcommand(payload)
            
        elif service == "mute":
            payload = "<Command><Audio><Microphones><Mute/></Microphones></Audio></Command>"
            await send_xcommand(payload)
            
        elif service == "unmute":
            payload = "<Command><Audio><Microphones><Unmute/></Microphones></Audio></Command>"
            await send_xcommand(payload)
            
        elif service == "set_volume":
            volume = call.data.get("volume")
            payload = f"<Configuration><Audio><Sounds><Volume>{volume}</Volume></Sounds></Configuration>"
            await send_xcommand(payload)
            
        elif service == "standby_activate":
            payload = "<Command><Standby><Activate/></Standby></Command>"
            await send_xcommand(payload)
            
        elif service == "standby_deactivate":
            payload = "<Command><Standby><Deactivate/></Standby></Command>"
            await send_xcommand(payload)

    # Registrierung der Dienste in Home Assistant
    hass.services.async_register(DOMAIN, "dial", handle_cisco_service)
    hass.services.async_register(DOMAIN, "disconnect", handle_cisco_service)
    hass.services.async_register(DOMAIN, "mute", handle_cisco_service)
    hass.services.async_register(DOMAIN, "unmute", handle_cisco_service)
    hass.services.async_register(DOMAIN, "set_volume", handle_cisco_service)
    hass.services.async_register(DOMAIN, "standby_activate", handle_cisco_service)
    hass.services.async_register(DOMAIN, "standby_deactivate", handle_cisco_service)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt einen Config Entry und deregistriert Dienste sowie Plattformen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        for service in ["dial", "disconnect", "mute", "unmute", "set_volume", "standby_activate", "standby_deactivate"]:
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)
                
    return unload_ok
