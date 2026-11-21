"""Cisco Video System Integration für Home Assistant."""
import html
import logging
import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

SERVICES = (
    "dial",
    "disconnect",
    "mute",
    "unmute",
    "set_volume",
    "standby_activate",
    "standby_deactivate",
    "standby_halfwake",
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setzt die Cisco Video System Integration aus einem Config Entry auf."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Zentrale Funktion zum Senden der XML-Befehle an /putxml
    async def send_xcommand(xml_payload: str):
        session = async_get_clientsession(hass)

        cleaned_host = host
        if not cleaned_host.startswith(("http://", "https://")):
            cleaned_host = f"https://{cleaned_host}"
        url = f"{cleaned_host.rstrip('/')}/putxml"

        auth = aiohttp.BasicAuth(username, password)
        headers = {"Content-Type": "text/xml"}

        try:
            async with session.post(
                url, data=xml_payload, auth=auth, headers=headers, ssl=False
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    _LOGGER.debug("Cisco API Antwort: %s", text)
                else:
                    _LOGGER.error(
                        "Fehler beim Senden an Cisco API. Status: %s", response.status
                    )
        except Exception as err:
            _LOGGER.error("Verbindungsfehler zur Cisco API: %s", err)

    hass.data[DOMAIN][entry.entry_id] = {
        "send_command": send_xcommand,
        "host": host,
    }

    # Hilfsfunktion, um den Befehl an alle konfigurierten Cisco-Geräte zu senden
    async def _send_to_all(xml_payload: str):
        for entry_data in hass.data[DOMAIN].values():
            await entry_data["send_command"](xml_payload)

    # Service-Handler definieren
    async def handle_dial(call: ServiceCall) -> None:
        target = html.escape(str(call.data.get("target", "")).strip())
        if not target:
            _LOGGER.error("Kein Anrufziel (target) angegeben.")
            return
        xml_payload = f"<Command><Dial><Number>{target}</Number></Dial></Command>"
        await _send_to_all(xml_payload)

    async def handle_disconnect(call: ServiceCall) -> None:
        await _send_to_all("<Command><Call><Disconnect/></Call></Command>")

    async def handle_mute(call: ServiceCall) -> None:
        await _send_to_all("<Command><Audio><Microphones><Mute/></Microphones></Audio></Command>")

    async def handle_unmute(call: ServiceCall) -> None:
        await _send_to_all("<Command><Audio><Microphones><Unmute/></Microphones></Audio></Command>")

    async def handle_set_volume(call: ServiceCall) -> None:
        volume = int(call.data.get("volume", 50))
        volume = max(0, min(100, volume))
        xml_payload = f"<Command><Audio><Volume><Set><Level>{volume}</Level></Set></Volume></Audio></Command>"
        await _send_to_all(xml_payload)

    async def handle_standby_activate(call: ServiceCall) -> None:
        await _send_to_all("<Command><Standby><Activate/></Standby></Command>")

    async def handle_standby_deactivate(call: ServiceCall) -> None:
        await _send_to_all("<Command><Standby><Deactivate/></Standby></Command>")

    async def handle_standby_halfwake(call: ServiceCall) -> None:
        await _send_to_all("<Command><Standby><Halfwake/></Standby></Command>")

    async def handle_signage_show(call: ServiceCall) -> None:
        await _send_to_all(
            "<Configuration><Standby><Signage><Mode>On</Mode></Signage></Standby></Configuration>"
        )
        await _send_to_all("<Command><Standby><Halfwake/></Standby></Command>")

    # Dienste registrieren (falls noch nicht geschehen)
    if not hass.services.has_service(DOMAIN, "dial"):
        hass.services.async_register(DOMAIN, "dial", handle_dial)
        hass.services.async_register(DOMAIN, "disconnect", handle_disconnect)
        hass.services.async_register(DOMAIN, "mute", handle_mute)
        hass.services.async_register(DOMAIN, "unmute", handle_unmute)
        hass.services.async_register(DOMAIN, "set_volume", handle_set_volume)
        hass.services.async_register(DOMAIN, "standby_activate", handle_standby_activate)
        hass.services.async_register(DOMAIN, "standby_deactivate", handle_standby_deactivate)
        hass.services.async_register(DOMAIN, "standby_halfwake", handle_standby_halfwake)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, wenn Optionen im Konfigurations-Button geändert und gespeichert werden."""
    _LOGGER.debug("Optionen geändert. Integration '%s' wird live neu geladen.", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt einen Config Entry und deregistriert alle Plattformen sauber."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Dienste nur entfernen, wenn keine weiteren Cisco-Geräte mehr aktiv sind
        if not hass.data[DOMAIN]:
            for service in SERVICES:
                hass.services.async_remove(DOMAIN, service)

    return unload_ok
