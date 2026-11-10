"""Zentrale API-Verbindungsklasse für das Cisco Videosystem."""
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

class CiscoVideoSystemAPI:
    """Wrapper für die lokale Cisco xAPI over HTTP."""

    def __init__(self, host: str, username: str, password: str, session: aiohttp.ClientSession):
        """Initialisiere die API-Verbindung."""
        self.host = host
        self.auth = aiohttp.BasicAuth(username, password)
        self.session = session
        self.base_url = f"https://{host}/api"

    async def send_command(self, endpoint: str, payload: dict = None) -> bool:
        """Sendet einen POST-Befehl an die Cisco xAPI."""
        url = f"{self.base_url}/command/{endpoint}"
        try:
            async with self.session.post(
                url, 
                auth=self.auth, 
                json=payload or {}, 
                ssl=False  # Cisco-Systeme nutzen oft selbstsignierte Zertifikate
            ) as response:
                if response.status in (200, 201, 204):
                    _LOGGER.debug("Befehl erfolgreich an %s gesendet", endpoint)
                    return True
                _LOGGER.error("Fehler beim Senden an %s: Status %s", endpoint, response.status)
                return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Netzwerkfehler bei Verbindung zu Cisco System: %s", err)
            return False

    async def dial(self, number: str) -> bool:
        """Einen Anruf starten."""
        return await self.send_command("Dial", {"Number": number})

    async def hangup(self) -> bool:
        """Alle aktiven Anrufe beenden."""
        return await self.send_command("Call/Disconnect", {"CallId": 0})

    async def set_volume(self, level: int) -> bool:
        """Lautstärke setzen (0 bis 100)."""
        return await self.send_command("Audio/Volume/Set", {"Level": level})

    async def mute_microphones(self, mute: bool) -> bool:
        """Mikrofone stummschalten oder Freigeben."""
        endpoint = "Audio/Microphones/Mute" if mute else "Audio/Microphones/Unmute"
        return await self.send_command(endpoint)

    async def set_standby(self, activate: bool) -> bool:
        """Standby-Modus aktivieren oder deaktivieren."""
        endpoint = "Standby/Activate" if activate else "Standby/Deactivate"
        return await self.send_command(endpoint)

