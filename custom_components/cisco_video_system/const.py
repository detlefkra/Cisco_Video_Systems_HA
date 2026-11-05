DOMAIN = "cisco_video_system"

CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SENSORS = "selected_sensors"

# Auswählbare Diagnose- und Statuswerte
AVAILABLE_SENSORS = {
    "system_unit_software_version": "Software Version",
    "status_peripherals_connected": "Angeschlossene Geräte",
    "status_network_ipv4_address": "IP-Adresse",
    "status_call_status": "Anruf-Status",
    "status_audio_volume": "Lautstärke",
    "status_standby_status": "Standby-Status"
}
