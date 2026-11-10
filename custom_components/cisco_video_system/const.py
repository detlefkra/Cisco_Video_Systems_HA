DOMAIN = "cisco_video_system"

CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SENSORS = "selected_sensors"

# Alle auswählbaren Diagnose-, Status- und Raumanalysewerte
AVAILABLE_SENSORS = {
    "system_unit_software_version": "Software Version",
    "status_peripherals_connected": "Angeschlossene Geräte",
    "status_network_ipv4_address": "IP-Adresse",
    "status_audio_volume": "Lautstärke",
    "status_standby_status": "Standby-Status",
    "room_temperature": "Temperatur",
    "room_humidity": "Luftfeuchte",
    "room_in_use": "In Use",
    "room_presence": "Presence",
    "room_noise": "Noise",
    "room_people_count": "People",
    "status_call_status": "Active Calls",
    "lightning_conditions": "LightingConditions"
}
