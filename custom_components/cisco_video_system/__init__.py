"""Die Cisco Video System Integration für Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CiscoVideoSystemAPI
from .const import DOMAIN, PLATFORMS  # Falls PLATFORMS in const.py definiert ist, z. B. ["sensor"]
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet das Cisco Video System aus einem Config Entry ein."""
    hass.data.setdefault(DOMAIN, {})

    # Holt die geteilte aiohttp-Clientsession von Home Assistant
    session = async_get_clientsession(hass)

    # Initialisiere die API-Verbindungsklasse mit den Daten aus dem Config Flow
    api = CiscoVideoSystemAPI(
        host=entry.data["host"],
        username=entry.data["username"],
        password=entry.data["password"],
        session=session
    )

    # Speichert die API-Instanz, damit services.py und sensor.py darauf zugreifen können
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api
    }

    # Leitet das Setup an deine Plattformen (z. B. sensor.py) weiter
    # Falls PLATFORMS in deiner const.py fehlt, kannst du auch ["sensor"] direkt eintragen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Registriere die neuen Dienste zur Steuerung (Dial, Mute, Volume, Standby etc.)
    async_setup_services(hass)

    _LOGGER.info("Cisco Video System Integration erfolgreich geladen.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt einen Config Entry (wichtig bei Deinstallation/Neustart der Integration)."""
    # Entfernt die Plattformen
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Bereinigt den globalen Speicher
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
