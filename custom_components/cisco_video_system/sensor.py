import logging
import xml.etree.ElementTree as ET
import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, AVAILABLE_SENSORS

_LOGGER = logging.getLogger(__name__)

# Mapping der Sensoren auf die exakten XML-Pfade der Cisco RoomOS status.xml
XML_PATHS = {
    "system_unit_software_version": "SystemUnit/Software/Version",
    "status_peripherals_connected": "Peripherals/ConnectedDevices",
    "status_network_ipv4_address": "Network/IPv4/Address",
    "status_call_status": "SystemUnit/State/NumberOfActiveCalls",
    "status_audio_volume": "Audio/Volume",
    "status_standby_status": "SystemUnit/State/Standby/Status"
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Erstellt die Sensoren basierend auf der Benutzerauswahl."""
    config = hass.data[DOMAIN][entry.entry_id]
    
    selected_sensors = entry.options.get(CONF_SENSORS, list(AVAILABLE_SENSORS.keys()))

    entities = []
    for sensor_key in selected_sensors:
        entities.append(CiscoSensor(config, sensor_key))

    async_add_entities(entities, update_before_add=True)


class CiscoSensor(SensorEntity):
    """Repräsentiert einen Cisco xAPI Diagnose-Sensor."""

    def __init__(self, config, sensor_key):
        self._host = config[CONF_HOST]
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]
        self._sensor_key = sensor_key
        
        self._attr_name = f"Cisco {AVAILABLE_SENSORS[sensor_key]}"
        self._attr_unique_id = f"cisco_{self._host}_{sensor_key}"
        self._attr_state = None

    async def async_update(self) -> None:
        """Holt Daten direkt vom Cisco-System via HTTPS XML-API."""
        # Auf HTTPS umgestellt, da dein System auf Port 443 lauscht
        url = f"https://{self._host}/status.xml" 
        auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            # WICHTIG: Hier erlauben wir selbstsignierte Zertifikate (ssl=False)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                with async_timeout.timeout(10):
                    async with session.get(url, auth=auth) as response:
                        if response.status == 200:
                            xml_data = await response.text()
                            
                            # XML parsen
                            root = ET.fromstring(xml_data)
                            
                            # Suchpfad für diesen spezifischen Sensor holen
                            xpath = XML_PATHS.get(self._sensor_key)
                            element = root.find(xpath)
                            
                            if element is not None and element.text is not None:
                                self._attr_state = element.text
                            else:
                                self._attr_state = "Nicht verfügbar"
                                _LOGGER.debug("Pfad %s im XML nicht gefunden", xpath)
                        else:
                            self._attr_state = f"API Fehler ({response.status})"
        except Exception as e:
            _LOGGER.error("Fehler beim Abruf der Cisco API für %s: %s", self._host, e)
            self._attr_state = "Nicht erreichbar"
