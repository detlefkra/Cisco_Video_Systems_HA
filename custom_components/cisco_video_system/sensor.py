import logging
import xml.etree.ElementTree as ET
import aiohttp
import asyncio

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
    "status_standby_status": "/Status/Standby/State"  # Korrigiert für RoomOS 11
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
        self._attr_state = "Initialisierung..."

    async def async_update(self) -> None:
        """Holt gezielt den gefilterten Wert vom Cisco-System via HTTPS."""
        xpath = XAPI_PATHS.get(self._sensor_key)
        if not xpath:
            self._attr_state = "Fehlerhafter Pfad"
            return

        url = f"https://{self._host}/getxml?location={xpath}"
        auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Timeout direkt über aiohttp steuern (verhindert Kompatibilitätsprobleme mit async_timeout)
                async with session.get(url, auth=auth, timeout=5) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        
                        if not xml_data.strip():
                            self._attr_state = "Leere API Antwort"
                            return

                        root = ET.fromstring(xml_data)
                        
                        # Definiere das gesuchte Ziel-Tag (z. B. "Version" oder "State")
                        target_tag = xpath.split("/")[-1]
                        
                        # Suche rekursiv im gesamten XML-Baum nach dem Element
                        found_element = None
                        for elem in root.iter():
                            if elem.tag == target_tag:
                                found_element = elem
                                break
                        
                        if found_element is not None and found_element.text is not None:
                            self._attr_state = found_element.text.strip()
                        else:
                            # Falls das Tag nicht existiert, nimm den ersten verfügbaren Textwert (Fallback)
                            fallback_value = None
                            for elem in root.iter():
                                if elem.text and elem.text.strip():
                                    fallback_value = elem.text.strip()
                            
                            self._attr_state = fallback_value if fallback_value else "Wert nicht im XML"
                    else:
                        self._attr_state = f"HTTP {response.status}"
        except asyncio.TimeoutError:
            self._attr_state = "Timeout (Verbindung lahm)"
        except ET.ParseError:
            self._attr_state = "XML Parsing Fehler"
        except Exception as e:
            _LOGGER.error("Fehler bei Cisco Update (%s): %s", self._sensor_key, e)
            self._attr_state = "Verbindungsfehler"
