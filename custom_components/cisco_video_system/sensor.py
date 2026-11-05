import logging
import xml.etree.ElementTree as ET
import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, AVAILABLE_SENSORS

_LOGGER = logging.getLogger(__name__)

# Die korrigierten und offiziellen xAPI-Pfade für Cisco RoomOS (z.B. Desk Pro)
XAPI_PATHS = {
    "system_unit_software_version": "/Status/SystemUnit/Software/Version",
    "status_peripherals_connected": "/Status/Peripherals/ConnectedDevices",
    "status_network_ipv4_address": "/Status/Network/IPv4/Address",
    "status_call_status": "/Status/SystemUnit/State/NumberOfActiveCalls",
    "status_audio_volume": "/Status/Audio/Volume",
    "status_standby_status": "/Status/Standby/State"
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

    # update_before_add=True zwingt HA, die Daten direkt vor dem Registrieren zu holen
    async_add_entities(entities, update_before_add=True)


class CiscoSensor(SensorEntity):
    """Repräsentiert einen Cisco xAPI Diagnose-Sensor."""

    def __init__(self, config, sensor_key):
        self._host = config[CONF_HOST]
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]
        self._sensor_key = sensor_key
        
        # Basis-Eigenschaften
        self._name = f"Cisco {AVAILABLE_SENSORS[sensor_key]}"
        self._unique_id = f"cisco_{self._host}_{sensor_key}"
        self._state_value = "Warte auf Update..."

    @property
    def name(self) -> str:
        """Gibt den Namen des Sensors zurück."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Gibt die eindeutige ID zurück."""
        return self._unique_id

    @property
    def state(self):
        """Gibt den aktuellen Zustand an Home Assistant weiter."""
        return self._state_value

    async def async_update(self) -> None:
        """Holt gezielt den gefilterten Wert vom Cisco-System via HTTPS."""
        xpath = XAPI_PATHS.get(self._sensor_key)
        if not xpath:
            self._state_value = "Fehlerhafter Pfad"
            return

        url = f"https://{self._host}/getxml?location={xpath}"
        auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            # Verbindung aufbauen (Unterstützung für selbstsignierte Zertifikate)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Nutze integrierten Timeout-Parameter von aiohttp
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(url, auth=auth, timeout=timeout) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        
                        if not xml_data.strip():
                            self._state_value = "Leere API Antwort"
                            return

                        root = ET.fromstring(xml_data)
                        target_tag = xpath.split("/")[-1]
                        
                        # XML-Struktur nach dem Ziel-Tag durchsuchen
                        found_element = None
                        for elem in root.iter():
                            if elem.tag == target_tag:
                                found_element = elem
                                break
                        
                        if found_element is not None and found_element.text is not None:
                            self._state_value = found_element.text.strip()
                        else:
                            # Fallback: Ersten gefundenen Textwert nutzen
                            fallback_value = None
                            for elem in root.iter():
                                if elem.text and elem.text.strip():
                                    fallback_value = elem.text.strip()
                            
                            self._state_value = fallback_value if fallback_value else "Kein Wert gefunden"
                    else:
                        self._state_value = f"HTTP Fehler {response.status}"
        except Exception as e:
            _LOGGER.error("Fehler bei Cisco API Update (%s): %s", self._sensor_key, e)
            self._state_value = "Verbindungsfehler"
