import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SENSORS, AVAILABLE_SENSORS

_LOGGER = logging.getLogger(__name__)

# Die XML-Tags, nach denen im zentralen Koordinator-Baum gesucht werden soll
TARGET_TAGS = {
    "system_unit_software_version": "Version",
    "status_peripherals_connected": "ConnectedDevices",
    "status_network_ipv4_address": "Address",
    "status_audio_volume": "Volume",
    "status_standby_status": "State",
    "room_temperature": "AmbientTemperature",
    "room_humidity": "RelativeHumidity",
    "room_in_use": "RoomInUse",
    "room_presence": "PeoplePresence",
    "room_noise": "A", # Das tiefste Element unter AmbientNoise/Level/A
    "room_people_count": "Current",
    "status_call_status": "NumberOfActiveCalls"
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Erstellt die Sensoren basierend auf dem zentralen Koordinator."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selected_sensors = entry.options.get(CONF_SENSORS, list(AVAILABLE_SENSORS.keys()))

    entities = []
    for sensor_key in selected_sensors:
        if sensor_key in TARGET_TAGS:
            entities.append(CiscoSensor(coordinator, sensor_key))

    async_add_entities(entities)


class CiscoSensor(CoordinatorEntity, SensorEntity):
    """Repräsentiert einen Cisco Sensor, gekoppelt an den zentralen Koordinator."""

    def __init__(self, coordinator, sensor_key):
        """Initialisiert den Sensor und verknüpft ihn mit dem Koordinator."""
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._host = coordinator.host
        
        self._name = f"Cisco {AVAILABLE_SENSORS[sensor_key]}"
        self._unique_id = f"cisco_{self._host}_{sensor_key}"

        # Einheiten-Zuweisung
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
        """Liest den Zustand direkt aus dem vom Koordinator frisch geholten XML-Baum."""
        if self.coordinator.data is None:
            return "Keine Daten"

        target_tag = TARGET_TAGS.get(self._sensor_key)
        
        # Rekursive Suche im lokal gespeicherten XML-Baum (verursacht 0 Last!)
        for elem in self.coordinator.data.iter():
            if elem.tag == target_tag:
                if elem.text and elem.text.strip():
                    return elem.text.strip()

        return "Nicht im XML gefunden"
