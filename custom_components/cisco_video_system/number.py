import logging
import xml.etree.ElementTree as ET
import aiohttp

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setzt den Lautstärkeregler für das Cisco System auf."""
    data = hass.data[DOMAIN][entry.entry_id]
    send_command = data["send_command"]
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    async_add_entities(
        [CiscoVolumeNumber(hass, entry, host, username, password, send_command)],
        update_before_add=True,  # Ruft den echten Wert direkt beim Start ab
    )


class CiscoVolumeNumber(NumberEntity):
    """Lautstärkeregler-Entität für das Cisco System."""

    def __init__(self, hass, entry, host, username, password, send_command):
        self.hass = hass
        self._send_command = send_command
        self._host = host
        self._username = username
        self._password = password

        self._attr_name = "Cisco Lautstärke"
        self._attr_unique_id = f"{entry.entry_id}_volume"
        self._attr_icon = "mdi:volume-high"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_value = None  # Kein fester Dummy-Wert mehr

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cisco Video System ({host})",
            manufacturer="Cisco",
            model="RoomOS Device",
        )

    async def async_update(self) -> None:
        """Liest die aktuelle Lautstärke vom Cisco-System aus."""
        session = async_get_clientsession(self.hass)
        cleaned_host = self._host
        if not cleaned_host.startswith(("http://", "https://")):
            cleaned_host = f"https://{cleaned_host}"
        url = f"{cleaned_host.rstrip('/')}/getxml?location=/Status/Audio/Volume"

        auth = aiohttp.BasicAuth(self._username, self._password)

        try:
            async with session.get(url, auth=auth, ssl=False) as response:
                if response.status == 200:
                    xml_text = await response.text()
                    root = ET.fromstring(xml_text)
                    volume_node = root.find(".//Volume")
                    if volume_node is not None and volume_node.text is not None:
                        self._attr_native_value = float(volume_node.text)
                else:
                    _LOGGER.debug(
                        "Fehler beim Abrufen der Lautstärke. Status: %s", response.status
                    )
        except Exception as err:
            _LOGGER.debug("Verbindungsfehler beim Abrufen der Lautstärke: %s", err)

    async def async_set_native_value(self, value: float) -> None:
        """Wird aufgerufen, wenn der Regler in HA verschoben wird."""
        volume_int = max(0, min(100, int(value)))
        payload = f"<Command><Audio><Volume><Set><Level>{volume_int}</Level></Set></Volume></Audio></Command>"
        await self._send_command(payload)
        self._attr_native_value = float(volume_int)
        self.async_write_ha_state()
