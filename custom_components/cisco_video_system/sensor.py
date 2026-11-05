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

# Die exakten xAPI-Pfade für Cisco RoomOS
XAPI_PATHS = {
    "system_unit_software_version": "/Status/SystemUnit/Software/Version",
    "status_peripherals_connected": "/Status/Peripherals/ConnectedDevices",
    "status_network_ipv4_address": "/Status/Network/IPv4/Address",
    "status_call_status": "/Status/SystemUnit/State/NumberOfActiveCalls",
    "status_audio_volume": "/Status/Audio/Volume",
    "status_standby_status": "/Status/SystemUnit/State/Standby/Status"
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
        """Holt gezielt den gefilterten Wert vom Cisco-System via HTTPS."""
        xpath = XAPI_PATHS.get(self._sensor_key)
        if not xpath:
            return

        # Wir nutzen den getxml-Endpunkt für gezielte Abfragen
        url = f"https://{self._host}/getxml?location={xpath}" 
        auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                with async_timeout.timeout(5):
                    async with session.get(url, auth=auth) as response:
                        if response.status == 200:
                            xml_data = await response.text()
                            root = ET.fromstring(xml_data)
                            
                            # Da getxml nur die Zielstruktur liefert, iterieren wir durch,
                            # bis wir das tiefste Element mit Inhalt finden.
                            value = None
                            for elem in root.iter():
                                if elem.text and not elem.text.strip() == "":
                                    # Verhindert, dass wir aus Versehen Whitespaces/Zeilenumbrüche parsen
                                    text_clean = elem.text.strip()
                                    if text_clean:
                                        value = text_clean

                            if value is not None:
                                self._attr_state = value
                            else:
                                self._attr_state = "Unbekannt"
                        else:
                            self._attr_state = f"API Fehler ({response.status})"
        except Exception as e:
            _LOGGER.error("Fehler beim Abruf von %s für %s: %s", xpath, self._host, e)
            self._attr_state = "Nicht erreichbar"
