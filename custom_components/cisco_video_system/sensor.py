import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_SENSORS, AVAILABLE_SENSORS

_LOGGER = logging.getLogger(__name__)

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
    "room_noise": "A",
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
            entities.append(CiscoSensor(coordinator, sensor_key, entry))

    async_add_entities(entities)


class CiscoSensor(CoordinatorEntity, SensorEntity):
    """Repräsentiert einen Cisco Sensor, gekoppelt an den zentralen Koordinator."""

    def __init__(self, coordinator, sensor_key, entry: ConfigEntry):
        """Initialisiert den Sensor und verknüpft ihn mit dem Koordinator."""
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._host = coordinator.host
        self._entry = entry
        
        self._name = f"Cisco {AVAILABLE_SENSORS[sensor_key]}"
        self._unique_id = f"cisco_{self._host}_{sensor_key}"
        self._last_valid_value = "Warte auf Update..."

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
    def device_info(self) -> DeviceInfo:
        """Verknüpft alle Sensoren zu einem einzigen, gemeinsamen Gerät."""
        # WICHTIG: Die Domain MUSS exakt 'cisco_device_control' lauten,
        # damit Home Assistant die Entitäten dem richtigen Gerät zuordnet.
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Cisco Desk Pro ({self._host})",
            manufacturer="Cisco",
            model="Webex RoomOS Device",
            configuration_url=f"https://{self._host}",
        )

    @property
    def state(self):
        """Liest den Zustand aus dem XML."""
        if self.coordinator.data is None:
            return self._last_valid_value

        target_tag = TARGET_TAGS.get(self._sensor_key)
        
        for elem in self.coordinator.data.iter():
            if elem.tag == target_tag:
                if elem.text and elem.text.strip():
                    self._last_valid_value = elem.text.strip()
                    return self._last_valid_value

        return self._last_valid_value
