"""Sensor-Plattform für das Cisco Video System mit konfigurierbaren Original-Sensoren."""
import logging
import xml.etree.ElementTree as ET
import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Deine originalen Sensor-Pfade (Exakt beibehalten)
TARGET_PATHS = {
    "system_unit_software_version": "SystemUnit/Software/Version",
    "status_peripherals_connected": "Cameras/Camera/Connected",  
    "status_network_ipv4_address": "Network/IPv4/Address",
    "status_audio_volume": "Audio/Volume",
    "status_standby_status": "Standby/State",
    "room_temperature": "RoomAnalytics/AmbientTemperature",
    "room_humidity": "RoomAnalytics/RelativeHumidity",
    "room_in_use": "RoomAnalytics/RoomInUse",
    "room_presence": "RoomAnalytics/PeoplePresence",
    "room_noise": "RoomAnalytics/AmbientNoise/Level/A",
    "room_people_count": "RoomAnalytics/PeopleCount/Current",
    "status_call_status": "SystemUnit/State/NumberOfActiveCalls",
    "lightning_conditions": "RoomAnalytics/LightingConditions",
    "camera_lid": "SystemUnit/State/CameraLid"
}

# Menschlich lesbare Namen und Icons für deine alten Sensoren
SENSOR_META = {
    "system_unit_software_version": {"name": "Software Version", "icon": "mdi:cloud-download"},
    "status_peripherals_connected": {"name": "Kamera verbunden", "icon": "mdi:video"},
    "status_network_ipv4_address": {"name": "IPv4 Adresse", "icon": "mdi:lan"},
    "status_audio_volume": {"name": "Lautstärke Status", "icon": "mdi:volume-high"},
    "status_standby_status": {"name": "Standby Status", "icon": "mdi:power-sleep"},
    "room_temperature": {"name": "Raumtemperatur", "icon": "mdi:thermometer"},
    "room_humidity": {"name": "Luftfeuchtigkeit", "icon": "mdi:water-percent"},
    "room_in_use": {"name": "Raum belegt", "icon": "mdi:door-closed-lock"},
    "room_presence": {"name": "Präsenz erkannt", "icon": "mdi:account-group"},
    "room_noise": {"name": "Umgebungsgeräusch", "icon": "mdi:ear-hearing"},
    "room_people_count": {"name": "Anzahl Personen", "icon": "mdi:account-badge"},
    "status_call_status": {"name": "Aktive Anrufe", "icon": "mdi:phone-in-talk"},
    "lightning_conditions": {"name": "Lichtverhältnisse", "icon": "mdi:white-balance-sunny"},
    "camera_lid": {"name": "Kameraabdeckung", "icon": "mdi:eye-off"}
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setzt die Cisco Sensor-Entitäten basierend auf dem Konfigurationsbutton auf."""
    data = hass.data[DOMAIN][entry.entry_id]
    host = data["host"]

    # Holt die Schlüssel der ausgewählten Sensoren aus den Optionen (z.B. ["room_temperature", "room_noise"])
    # Falls das Feld leer oder neu ist, werden als Fallback einfach ALLE Sensoren geladen
    selected_sensors = entry.options.get("selected_sensors", list(TARGET_PATHS.keys()))

    entities = []
    
    # Geht alle ausgewählten Sensoren durch und baut sie auf
    for key in selected_sensors:
        if key in TARGET_PATHS:
            xpath = TARGET_PATHS[key]
            meta = SENSOR_META.get(key, {"name": key.replace("_", " ").title(), "icon": "mdi:eye"})
            entities.append(CiscoConfigurableSensor(hass, entry, host, key, xpath, meta))

    async_add_entities(entities, update_before_add=True)


class CiscoConfigurableSensor(SensorEntity):
    """Repräsentiert einen über den Konfigurations-Button gewählten Sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, host: str, key: str, xpath: str, meta: dict):
        """Initialisiert den Sensor."""
        self.hass = hass
        self._entry = entry
        self._host = host
        self._key = key
        self._xpath = xpath
        
        self._attr_name = f"Cisco {meta['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = meta["icon"]
        self._attr_native_value = None

        # Passende Maßeinheiten zuweisen
        if "temperature" in key:
            self._attr_native_unit_of_measurement = "°C"
        elif "humidity" in key:
            self._attr_native_unit_of_measurement = "%"
        elif "noise" in key:
            self._attr_native_unit_of_measurement = "dBA"

        # Bietet die gemeinsame Geräte-Zuordnung
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cisco Video System ({host})",
            manufacturer="Cisco",
            model="RoomOS Device",
        )

    async def async_update(self) -> None:
        """Holt den aktuellen Wert über die Cisco /getxml Schnittstelle."""
        session = async_get_clientsession(self.hass)
        
        cleaned_host = self._host
        if not cleaned_host.startswith(("http://", "https://")):
            cleaned_host = f"https://{cleaned_host}"
            
        url = f"{cleaned_host.rstrip('/')}/getxml?location=/Status/{self._xpath}"
        
        username = self._entry.data.get("username")
        password = self._entry.data.get("password")
        auth = aiohttp.BasicAuth(username, password)

        try:
            async with session.get(url, auth=auth, ssl=False, timeout=10) as response:
                if response.status == 200:
                    xml_text = await response.text()
                    root = ET.fromstring(xml_text)
                    
                    target_tag = self._xpath.split("/")[-1]
                    element = root.find(f".//{target_tag}")
                    
                    if element is not None and element.text is not None:
                        self._attr_native_value = element.text
                    else:
                        self._attr_native_value = None
                else:
                    _LOGGER.error("Fehler beim Abfragen von %s. Status: %s", self._xpath, response.status)
                    
        except Exception as err:
            _LOGGER.error("Verbindungsfehler beim Update von %s: %s", self._key, err)
