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

    buttons = [
        CiscoButton(entry, host, send_command, "disconnect", "Anruf beenden", "mdi:phone-hangup", "<Command><Call><Disconnect/></Call></Command>"),
        CiscoButton(entry, host, send_command, "mute", "Mikrofone stummschalten", "mdi:microphone-off", "<Command><Audio><Microphones><Mute/></Microphones></Audio></Command>"),
        CiscoButton(entry, host, send_command, "unmute", "Mikrofone einschalten", "mdi:microphone", "<Command><Audio><Microphones><Unmute/></Microphones></Audio></Command>"),
        CiscoButton(entry, host, send_command, "standby_activate", "System Standby", "mdi:power-sleep", "<Command><Standby><Activate/></Standby></Command>"),
        CiscoButton(entry, host, send_command, "standby_deactivate", "System Digital Signage", "mdi:power", "<Command><Standby><Signage><InteractionMode>Interactive</InteractionMode></Signage></Standby></Command>"),
        CiscoButton(entry, host, send_command, "standby_deactivate", "System Halfwake", "mdi:power", "<Command><Standby><Halfwake><Mode>Auto</Mode></Halfwake></Standby></Command>"),
        CiscoButton(entry, host, send_command, "standby_deactivate", "System Wake", "mdi:power", "<Command><Standby><Deactivate/></Standby></Command>"),        
        CiscoButton(entry, host, send_command, "input_2", "Input USB-C aktivieren", "mdi:video-input-hdmi", "<Command><Presentation><Start><ConnectorId>2</ConnectorId></Start></Presentation></Command>"),
        CiscoButton(entry, host, send_command, "input_3", "Input HDMI aktivieren", "mdi:video-input-hdmi", "<Command><Presentation><Start><ConnectorId>3</ConnectorId></Start></Presentation></Command>"),
        CiscoButton(entry, host, send_command, "presentation_stop", "Input Teilen beenden", "mdi:presentation-play", "<Command><Presentation><Stop/></Presentation></Command>"),
    ]

    async_add_entities(buttons)


class CiscoButton(ButtonEntity):
    """Repräsentiert einen Knopf auf der Cisco Geräteseite."""

    _attr_has_entity_name = True

    def __init__(self, entry, host, send_command, key, name, icon, payload):
        self._send_command = send_command
        self._payload = payload
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cisco Video System ({host})",
            manufacturer="Cisco",
            model="RoomOS Device",
        )

    async def async_press(self) -> None:
        """Wird ausgeführt, wenn der Button in HA gedrückt wird."""
        await self._send_command(self._payload)
