DOMAIN = "cisco_video_system"
PLATFORMS = ["sensor", "button", "number"]
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SENSORS = "selected_sensors"

# Alle auswählbaren Diagnose-, Status- und Raumanalysewerte
AVAILABLE_SENSORS = {
    "system_unit_software_version": "Software Version",
    "status_peripherals_connected": "Angeschlossene Geräte",
    "status_network_ipv4_address": "IP-Adresse",
    "status_audio_volume": "Audio Lautstärke",
    "status_standby_status": "Standby-Status",
    "room_temperature": "Temperatur",
    "room_humidity": "Luftfeuchte",
    "room_in_use": "In Benutzung",
    "room_presence": "Presence",
    "room_noise": "Raum Lautstärke",
    "room_people_count": "Personen",
    "status_call_status": "Active Calls",
    "lightning_conditions": "Lighting Conditions",
    "camera_lid": "Camera Klappe"
}
