import logging
import xml.etree.ElementTree as ET
from datetime import timedelta
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Integration über einen Config Entry auf."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = CiscoDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt die Integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Startet die Plattform neu, wenn sich die Sensor-Auswahl ändert."""
    await hass.config_entries.async_reload(entry.entry_id)


class CiscoDataCoordinator(DataUpdateCoordinator):
    """Zentraler Koordinator, der ALLE Werte mit nur EINEM API-Aufruf holt."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry = entry
        self.host = entry.data["host"]
        self.username = entry.data["username"]
        self.password = entry.data["password"]
        
        # Abfrage alle 30 Sekunden schont die Ressourcen des Cisco-Systems vollständig
        super().__init__(
            hass,
            _LOGGER,
            name=f"Cisco API {self.host}",
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self):
        """Holt den gesamten Status-Baum in einem einzigen, akkuschonenden Aufruf."""
        url = f"https://{self.host}/getxml?location=/Status"
        auth = aiohttp.BasicAuth(self.username, self.password)

        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                timeout = aiohttp.ClientTimeout(total=20)
                async with session.get(url, auth=auth, timeout=timeout) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        if not xml_data.strip():
                            raise UpdateFailed("Leere Antwort von Cisco API")
                        
                        return ET.fromstring(xml_data)
                    else:
                        raise UpdateFailed(f"HTTP Fehler {response.status}")
        except Exception as err:
            raise UpdateFailed(f"Verbindung zu Cisco fehlgeschlagen: {err}")
