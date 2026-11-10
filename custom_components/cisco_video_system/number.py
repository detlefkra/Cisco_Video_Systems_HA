from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setzt den Lautstärkeregler für das Cisco System auf."""
    data = hass.data[DOMAIN][entry.entry_id]
    send_command = data["send_command"]
    host = data["host"]

    async_add_entities([CiscoVolumeNumber(entry, host, send_command)])

class CiscoVolumeNumber(NumberEntity):
    """Lautstärkeregler-Entität für das Cisco System."""

    def __init__(self, entry, host, send_command):
        self._send_command = send_command
        self._attr_name = "Cisco Lautstärke"
        self._attr_unique_id = f"{entry.entry_id}_volume"
        self._attr_icon = "mdi:volume-high"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_value = 50  # Standard-Startwert (wird bei Updates überschrieben)
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cisco Video System ({host})",
            manufacturer="Cisco",
            model="RoomOS Device",
        )

    async def async_set_native_value(self, value: float) -> None:
        """Wird aufgerufen, wenn der Regler in HA verschoben wird."""
        volume_int = int(value)
        payload = f"<Configuration><Audio><Sounds><Volume>{volume_int}</Volume></Sounds></Configuration>"
        await self._send_command(payload)
        self._attr_native_value = value
        self.async_write_ha_state()

