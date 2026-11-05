import logging
import xml.etree.ElementTree as ET
import aiohttp

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, AVAILABLE_SENSORS

_LOGGER = logging.getLogger(__name__)

XAPI_PATHS = {
    "system_unit_software_version": "/Status/SystemUnit/Software/Version",
    "status_peripherals_connected": "/Status/Peripherals/ConnectedDevices",
    "status_network_ipv4_address": "/Status/Network/IPv4/Address",
    "status_audio_volume": "/Status/Audio/Volume",
    "status_standby_status": "/Status/Standby/State",
    "room_temperature": "/Status/RoomAnalytics/AmbientTemperature",
    "room_humidity": "/Status/RoomAnalytics/RelativeHumidity",
    "room_in_use": "/Status/RoomAnalytics/RoomInUse",
    "room_presence": "/Status/RoomAnalytics/PeoplePresence",
    "room_noise": "/Status/RoomAnalytics/AmbientNoise/Level/A",
    "room_people_count": "/Status/RoomAnalytics/PeopleCount/Current",
    "status_call_status": "/Status/SystemUnit/State/NumberOfActiveCalls"
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Erstellt die Sensoren basierend auf der Benutzerauswahl."""
    config = hass.data[DOMAIN][entry.entry_id]
    
    # Wenn Optionen existieren, nehmen wir diese. Wenn in den Optionen CONF_SENSORS fehlt,
    # laden wir zur Sicherheit direkt alle Keys aus AVAILABLE_SENSORS
    selected_sensors = entry.options.get(CONF_SENSORS)
    
    if selected_sensors is減_none oder len(selected_sensors) == 0:
        selected_sensors = list(AVAILABLE_SENSORS.keys())

    entities = []
    for sensor_key in selected_sensors:
        # Sicherheits-Check falls alte Optionen geladen wurden, aber der Pfad existiert
        if sensor_key in XAPI_PATHS:
            entities.append(CiscoSensor(config, sensor_key))

    async_add_entities(entities, update_before_add=True)


class CiscoSensor(SensorEntity):
    """Repräsentiert einen Cisco xAPI Diagnose-Sensor."""

    def __init__(self, config, sensor_key):
        self._host = config[CONF_HOST]
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]
        self._sensor_key = sensor_key
        
        self._name = f"Cisco {AVAILABLE_SENSORS[sensor_key]}"
        self._unique_id = f"cisco_{self._host}_{sensor_key}"
        self._state_value = "Warte auf Update..."

        # Dynamische Zuweisung von Maßeinheiten und Geräteklassen
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None

        if sensor_key == "room_temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = "°C"
        elif sensor_key == "room_humidity":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = "%"
        elif sensor_key == "room_noise":
            self._attr_device_class = SensorDeviceClass.SOUND_PRESSURE
            self._attr_native_unit_of_measurement = "dBA"

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def state(self):
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
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
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
