import logging
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SENSORS, AVAILABLE_SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Erstellt die Sensoren basierend auf der Benutzerauswahl."""
    config = hass.data[DOMAIN][entry.entry_id]
    
    # Nutze ausgewählte Sensoren aus den Optionen, falls vorhanden, sonst alle
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
        """Holt Daten direkt vom Cisco-System via HTTP JSON-API."""
        # Cisco RoomOS nutzt standardmäßig die HTTP-API unter /status.xml oder /getxml
        # Für JSON-Daten wird oft die /jsxapi Endpunkt verwendet.
        url = f"https://{self._host}/status.xml" 
        auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth, timeout=5) as response:
                    if response.status == 200:
                        # Dummy-Logik: Hier parst du das XML/JSON basierend auf self._sensor_key
                        # Beispiel für einen echten Payload-Abruf:
                        # data = await response.json()
                        
                        if self._sensor_key == "status_standby_status":
                            self._attr_state = "Standby"  # Beispielwert
                        elif self._sensor_key == "status_call_status":
                            self._attr_state = "Idle"
                        else:
                            self._attr_state = "Verbunden"
                    else:
                        self._attr_state = "API Error"
        except Exception as e:
            _LOGGER.error("Fehler beim Abruf der Cisco API für %s: %s", self._host, e)
            self._attr_state = "Nicht erreichbar"
