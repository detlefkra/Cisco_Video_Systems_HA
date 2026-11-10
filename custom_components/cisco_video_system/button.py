from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setzt die Button-Entitäten für das Cisco System auf."""
    data = hass.data[DOMAIN][entry.entry_id]
    send_command = data["send_command"]
    host = data["host"]

    # Alle Tasten, die auf dem Gerät erscheinen sollen
    buttons = [
        CiscoButton(entry, host, send_command, "disconnect", "Anruf beenden", "mdi:phone-hangup", "<Command><Call><Disconnect/></Call></Command>"),
        CiscoButton(entry, host, send_command, "mute", "Mikrofone stummschalten", "mdi:microphone-off", "<Command><Audio><Microphones><Mute/></Microphones></Audio></Command>"),
        CiscoButton(entry, host, send_command, "unmute", "Mikrofone einschalten", "mdi:microphone", "<Command><Audio><Microphones><Unmute/></Microphones></Audio></Command>"),
        CiscoButton(entry, host, send_command, "standby_activate", "Standby aktivieren", "mdi:power-sleep", "<Command><Standby><Activate/></Standby></Command>"),
        CiscoButton(entry, host, send_command, "standby_deactivate", "System aufwecken", "mdi:power", "<Command><Standby><Deactivate/></Standby></Command>"),
    ]
    
    async_add_entities(buttons)

class CiscoButton(ButtonEntity):
    """Repräsentiert einen Knopf auf der Cisco Geräteseite."""

    def __init__(self, entry, host, send_command, key, name, icon, payload):
        self._send_command = send_command
        self._payload = payload
        self._attr_name = f"Cisco {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        
        # Das bindet die Entität fest an das Hauptgerät in Home Assistant
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cisco Video System ({host})",
            manufacturer="Cisco",
            model="RoomOS Device",
        )

    async def async_press(self) -> None:
        """Wird ausgeführt, wenn der Button in HA gedrückt wird."""
        await self._send_command(self._payload)

