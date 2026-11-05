# Cisco Video System Integration for Home Assistant

[![hacs_badge]([https://shields.io](https://brands.home-assistant.io/_/marketplace//logo.png))](https://github.com)

Diese HACS-Integration ermöglicht die Diagnose und Steuerung von Cisco Videosystemen (RoomOS / Webex Devices) über die lokale Cisco HTTP-API.

## Features
- **Einfache Einrichtung:** Anmeldedaten und IP-Adresse direkt über die Home Assistant Benutzeroberfläche (Config Flow) eingeben.
- **Dynamische Sensorauswahl:** Wähle über die Integrationsoptionen flexibel aus, welche Diagnose- und Statuswerte als Sensoren angelegt werden sollen.
- **Lokale Steuerung:** Keine Cloud erforderlich, die Abfrage erfolgt direkt über dein lokales Netzwerk.

## Installation

### Über HACS (Empfohlen)
1. Öffne **HACS** in Home Assistant.
2. Klicke oben rechts auf die drei Punkte und wähle **Benutzerdefinierte Repositories** (Custom Repositories).
3. Füge die URL dieses GitHub-Repositories hinzu und wähle als Kategorie **Integration**.
4. Klicke auf **Herunterladen**.
5. Starte Home Assistant neu.

### Manuelle Installation
1. Lade den Ordner `custom_components/cisco_video_system` herunter.
2. Kopiere diesen Ordner in das Verzeichnis `/config/custom_components/` deiner Home Assistant Instanz.
3. Starte Home Assistant neu.

## Konfiguration

1. Gehe in Home Assistant zu **Einstellungen** -> **Geräte & Dienste**.
2. Klicke unten rechts auf **Integration hinzufügen**.
3. Suche nach **Cisco Video System**.
4. Gib die IP-Adresse/Host sowie Benutzernamen und Passwort deines Cisco-Systems ein.
5. Nach der Einrichtung kannst du auf **Konfigurieren** klicken, um die gewünschten Sensoren auszuwählen oder zu ändern.

## Voraussetzungen
Auf dem Cisco-System muss der HTTP-Server sowie die xAPI über HTTP aktiviert sein:
- `xConfiguration NetworkServices HTTP Mode: On`
- `xConfiguration NetworkServices HTTPS Mode: On` (empfohlen)
