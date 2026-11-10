"""Cisco Video System Integration für Home Assistant."""
import logging
import aiohttp
from homeassistant.core import HomeAssistant
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
    
    # Zentrale Funktion zum Senden der XML-Befehle an /putxml
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

    # Speichern des Befehls-Senders im Integrations-Kontext.
    hass.data[DOMAIN][entry.entry_id] = {
        "send_command": send_xcommand,
        "host": host
    }
    
    # KORREKTUR: Registriert den Update-Listener für den Konfigurations-Button mit der richtigen Methode
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    # Automatisiertes Laden aller registrierten Plattformen (sensor, button, number)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, wenn Optionen im Konfigurations-Button geändert und gespeichert werden."""
    _LOGGER.debug("Optionen geändert. Integration '%s' wird live neu geladen.", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt einen Config Entry und deregistriert alle Plattformen sauber."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Speicherplatz nach dem Deinstallieren/Deaktivieren wieder freigeben
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok
