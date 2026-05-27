# Webots Server Anleitung

Reproduzierbare Anleitung zum Betrieb eines Webots-Simulationsservers unter WSL2.
Grundlage ist die offizielle [Cyberbotics webots-server](https://github.com/cyberbotics/webots-server)-Architektur (R2025a).

---

## Protokoll und Architektur

```text
Externer Rechner (Client / Controller)
          |
          |  1. WebSocket ws://:1999/  → Verfügbarkeit prüfen (1 oder 0)
          |  2. HTTP GET  :1999/session → URL des Simulation Servers
          |  3. WebSocket :2000/client  → Simulation starten → Webots-URL
          |  4. WebSocket :2001+        → Webots direkt (Streaming / Steuerung)
          v
┌──────────────────────────────────────────────────────────┐
│  WSL2 (Ubuntu 24.04)                                     │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  session_server.py  :1999                           │ │
│  │  - Überwacht Last aller Simulation Server           │ │
│  │  - Gibt Client URL des am wenigsten belasteten      │ │
│  │    Simulation Servers zurück                        │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │  regelmäßige Last-Abfragen      │
│                         v                                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  simulation_server.py  :2000                        │ │
│  │  - Startet Webots-Instanz pro Client-Anfrage        │ │
│  │  - Klont Projektdateien von GitHub                  │ │
│  │  - Startet Docker-Container mit Webots              │ │
│  │  - Sendet Webots WebSocket-URL an Client            │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │  docker run                     │
│                         v                                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Docker-Instanz  :2001+  (eine pro Session)         │ │
│  │  Webots  ── Welt + Protos + Supervisor-Controller   │ │
│  │  Robot-Controller: <extern>                         │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**Ablauf einer Session (Protokoll):**

1. Client verbindet sich via WebSocket mit `ws://localhost:1999/` — Session Server antwortet mit `1` (verfügbar) oder `0` (nicht verfügbar). Ändert sich die Verfügbarkeit, sendet der Server automatisch eine Benachrichtigung.
2. Client sendet eine HTTP-Anfrage an `http://localhost:1999/session` — Session Server gibt die WebSocket-URL des am wenigsten belasteten Simulation Servers zurück.
3. Client verbindet sich via WebSocket mit `ws://localhost:2000/client` und schickt eine `start`-Nachricht mit der GitHub-URL der Weltdatei. Der Simulation Server klont das Projekt, startet Webots im Docker-Container und gibt die WebSocket-URL der Webots-Instanz zurück.
4. Client (und externer Robot-Controller) verbinden sich direkt mit der Webots-Instanz für Streaming und Steuerung.

> Der Session Server fragt die Simulation Server regelmäßig nach ihrer Systemlast ab (/load). Ist ein Server überlastet, wird er als nicht verfügbar markiert und nicht mehr an Clients vergeben.

---

## Schichtenübersicht

| Schicht | Prozess | Port | Aufgabe |
| --- | --- | --- | --- |
| Session Server | `session_server.py` | 1999 | Verfügbarkeit, Last-Balancing, Client-Routing |
| Simulation Server | `simulation_server.py` | 2000 | GitHub-Checkout, Docker-Start, Kapazität melden |
| Webots-Instanz | Docker-Container | 2001+ | Physik, Welt, Supervisor (eine pro Session) |
| Robot-Controller | Externer Rechner | — | Robotersteuerung via Webots-extern-Protokoll |

---

## Verzeichnisstruktur (WSL)

```text
~/
├── webots-server/                    ← Cyberbotics-Repo (Schritt 5)
│   ├── session_server.py
│   ├── simulation_server.py
│   ├── server.sh                     ← Hilfsskript zum Starten/Stoppen
│   └── config/
│       ├── session/
│       │   └── config.json           ← Schritt 6
│       └── simulation/
│           └── config.json           ← Schritt 7
│
└── <dein-projekt>/                   ← eigenes Repo (auf GitHub)
    ├── webots/
    │   ├── worlds/
    │   ├── protos/
    │   └── controllers/
    └── README.md
```

> Das Projektverzeichnis muss auf einem öffentlichen GitHub-Repository liegen,
> da der Simulation Server die Welt und Controller automatisch per `git clone` abruft.
> Native Linux-Pfade in WSL (`~/`) sind wegen besserer I/O-Performance zu bevorzugen.

---

## Voraussetzungen

- **Windows 11 22H2 oder neuer** (WSLg + mirrored networking)
- **WSL2** mit Ubuntu 24.04
- **Docker Desktop für Windows**
- Python 3.10+ (für Session und Simulation Server)
- Öffentliches GitHub-Repository mit der Webots-Welt

---

## Schritt 1: WSL2 und Ubuntu einrichten

In PowerShell als Administrator:

```powershell
wsl --install -d Ubuntu-24.04
```

Nach Abschluss Ubuntu starten und Benutzer anlegen (folgt dem interaktiven Prompt).

> Sind bereits andere WSL-Distributionen installiert, Ubuntu-24.04 als Standard setzen:

```powershell
wsl --set-default Ubuntu-24.04
```

---

## Schritt 2: Docker Desktop einrichten

1. [Docker Desktop für Windows](https://www.docker.com/products/docker-desktop/) installieren.
2. In Docker Desktop → Settings → Resources → WSL Integration:
   **Ubuntu-24.04** aktivieren.
3. In WSL2 ist `docker` danach direkt verfügbar — keine weitere Installation nötig.

**Überprüfung** (in WSL):

```bash
docker run --rm hello-world
```

---

## Schritt 3: Webots Docker-Images vorbereiten

Der Simulation Server startet Webots-Instanzen in Docker-Containern. Die Version des
Images wird automatisch aus der Kopfzeile der Weltdatei ermittelt (z.B. `#VRML_SIM R2025a utf8`).

```bash
# Standard-Image (empfohlen)
docker pull cyberbotics/webots.cloud:R2025a-ubuntu22.04

# Image mit NumPy-Unterstützung für Controller
docker pull cyberbotics/webots.cloud:R2025a-ubuntu22.04-numpy
```

> Webots-Versionen unter R2022b werden nicht unterstützt.

---

## Schritt 4: Robot-Controller auf `<extern>` umstellen

Damit der Controller auf einem externen Rechner laufen kann, muss in der Weltdatei
(`.wbt`) der Controller-Eintrag des Roboters auf `<extern>` gesetzt werden:

```text
DEF ROBOT MyRobot {
  ...
  controller "<extern>"
  ...
}
```

Webots wartet dann beim Start auf eine eingehende Controller-Verbindung.

---

## Schritt 5: webots-server Repository einrichten

```bash
# Systemabhängigkeiten
sudo apt update
sudo apt install -y python3-pip python3-venv python-is-python3 git subversion x11-xserver-utils

# Repository klonen
git clone https://github.com/cyberbotics/webots-server.git ~/webots-server

# Virtual Environment anlegen und Pakete installieren
python3 -m venv ~/webots-server/.venv
source ~/webots-server/.venv/bin/activate
pip install pynvml requests psutil tornado distro websockets
```

> Ubuntu 24.04 sperrt systemweite pip-Installationen (PEP 668).
> Die venv muss vor jedem Serverstart aktiviert werden:
> `source ~/webots-server/.venv/bin/activate`

---

## Schritt 6: Session Server konfigurieren

Konfigurationsdatei `~/webots-server/config/session/config.json` anlegen:

```json
{
  "port": 1999,
  "ssl": false,
  "portRewrite": false,
  "server": "localhost",
  "simulationServers": [
    "localhost/2000"
  ],
  "debug": true
}
```

**Alle verfügbaren Parameter:**

| Parameter | Beschreibung | Standard |
| --- | --- | --- |
| `port` | Lokaler Port des Session Servers | — |
| `ssl` | HTTPS/WSS-URLs verwenden | `true` |
| `portRewrite` | Port-Umschreibung durch Apache aktivieren | `true` |
| `server` | Vollqualifizierter Domainname des Session Servers | — |
| `simulationServers` | Liste der verfügbaren Simulation Server | — |
| `administrator` | E-Mail für Benachrichtigungen | — |
| `mailServer` | SMTP-Host für Benachrichtigungen | — |
| `mailServerPort` | SMTP-Port | — |
| `mailSender` | Absender-E-Mail | — |
| `mailSenderPassword` | Passwort des SMTP-Absenders | — |
| `logDir` | Verzeichnis für Log-Dateien | — |
| `debug` | Debug-Ausgaben auf stdout | `false` |

---

## Schritt 7: Simulation Server konfigurieren

Konfigurationsdatei `~/webots-server/config/simulation/config.json` anlegen:

```json
{
  "port": 2000,
  "ssl": false,
  "portRewrite": false,
  "server": "localhost",
  "docker": true,
  "webotsHome": "/usr/local/webots",
  "maxConnections": 5,
  "logDir": "log/",
  "debug": true
}
```

**Alle verfügbaren Parameter:**

| Parameter | Beschreibung | Standard |
| --- | --- | --- |
| `port` | Lokaler Port des Simulation Servers | — |
| `ssl` | HTTPS/WSS-URLs verwenden | `true` |
| `portRewrite` | Port-Umschreibung durch Apache aktivieren | `true` |
| `server` | Vollqualifizierter Domainname des Simulation Servers | — |
| `docker` | Webots in Docker-Container starten (empfohlen) | `false` |
| `allowedRepositories` | Liste erlaubter GitHub-Repositories | — |
| `blockedRepositories` | Liste gesperrter GitHub-Repositories | — |
| `persistantDockerImages` | Docker-Images, die nicht aus dem Cache entfernt werden | — |
| `shareIdleTime` | Max. Last für nicht erlaubte Repositories | `50%` |
| `notify` | Webservices für Server-Status-Benachrichtigungen | `https://webots.cloud` |
| `projectsDir` | Verzeichnis, in dem Projekte abgelegt werden | — |
| `webotsHome` | Installationspfad von Webots (`WEBOTS_HOME`) | — |
| `maxConnections` | Maximale Anzahl gleichzeitiger Webots-Instanzen | — |
| `logDir` | Verzeichnis für Log-Dateien | — |
| `monitorLogEnabled` | Monitor-Daten in Datei speichern | `true` |
| `debug` | Debug-Ausgaben auf stdout | `false` |
| `timeout` | Sekunden bis eine Simulation automatisch beendet wird | 7200 (min. 360) |

---

## Schritt 8: Server starten

### Option A: Über `server.sh` (empfohlen)

```bash
source ~/webots-server/.venv/bin/activate
cd ~/webots-server
./server.sh start config
```

Dies startet Session Server mit `config/session/config.json` und Simulation Server mit
`config/simulation/config.json`. Das Argument `config` entspricht dem Dateinamen ohne `.json`.
Zum Stoppen:

```bash
cd ~/webots-server
./server.sh stop
```

### Option B: Manuell in separaten Terminals

Terminal 1 — Simulation Server zuerst starten:

```bash
source ~/webots-server/.venv/bin/activate
python3 ~/webots-server/simulation_server.py ~/webots-server/config/simulation/config.json
```

Terminal 2 — Dann Session Server starten:

```bash
source ~/webots-server/.venv/bin/activate
python3 ~/webots-server/session_server.py ~/webots-server/config/session/config.json
```

> **Startreihenfolge beachten:** Der Simulation Server muss vor dem Session Server gestartet
> werden, damit der Session Server ihn beim Start direkt registrieren kann.

**Status prüfen:**

```text
http://localhost:1999/monitor   → Session Server Übersicht
http://localhost:2000/monitor   → Simulation Server Details (CPU, GPU, Netzwerk)
```

---

## Schritt 9: Simulation starten (von außen)

### Verfügbarkeit prüfen (WebSocket)

```python
import asyncio, websockets

async def check():
    async with websockets.connect('ws://localhost:1999/') as ws:
        msg = await ws.recv()
        print('Verfügbar:', msg)  # '1' oder '0'

asyncio.run(check())
```

### Simulation starten (HTTP + WebSocket)

Skript `start_session.py`:

```python
import asyncio
import json
import requests
import websockets

# Simulation Server URL vom Session Server holen (HTTP)
sim_url = requests.get("http://localhost:1999/session").text.strip()
print(f"Simulation Server: {sim_url}")
# Antwort: ws://localhost:2000

async def main():
    # ping_interval=None verhindert Timeout beim ersten git clone (~60 s)
    async with websockets.connect(sim_url + "/client", ping_interval=None) as ws:
        await ws.send(json.dumps({
            "start": {
                "url": "https://github.com/<owner>/<repo>/blob/<branch>/webots/worlds/<welt>.wbt"
            }
        }))
        # Der Server sendet zuerst mehrere "loading: ..."-Zeilen (kein JSON),
        # dann die eigentliche JSON-Antwort mit der Webots-URL.
        while True:
            msg = await ws.recv()
            try:
                response = json.loads(msg)
                print(response)
                # { "url": "ws://localhost:2001", ... }
                break
            except json.JSONDecodeError:
                print(msg)  # z.B. "loading: Pulling Docker image..."

asyncio.run(main())
```

```bash
python3 start_session.py
```

**Format der `start`-Nachricht:**

```json
{
  "start": {
    "url": "https://github.com/alice/sim/blob/main/worlds/my_world.wbt",
    "mode": "w3d"
  }
}
```

| Feld | Wert | Beschreibung |
| --- | --- | --- |
| `url` | GitHub-URL zur `.wbt`-Datei | Pflichtfeld |
| `mode` | `w3d` (Standard) oder `mjpeg` | Optional |

> Der Simulation Server erkennt Branch/Tag automatisch aus der URL und klont nur
> das notwendige Unterverzeichnis via `svn checkout` (nicht das gesamte Repository).

Die Antwort enthält die WebSocket-URL der gestarteten Webots-Instanz.

---

## Verbindungsübersicht

| Verbindung | Protokoll | Port | Richtung | Zweck |
| --- | --- | --- | --- | --- |
| Client → Session Server `/` | WebSocket | 1999 | Client → Server | Verfügbarkeit prüfen (1 oder 0) |
| Client → Session Server `/monitor` | HTTP GET | 1999 | Client → Server | Statusübersicht |
| Client → Session Server `/session` | HTTP GET | 1999 | Client → Server | URL des Simulation Servers erhalten |
| Session Server → Simulation Server `/load` | HTTP GET | 2000 | Server intern | Last abfragen |
| Client → Simulation Server `/client` | WebSocket | 2000 | Client → Server | Simulation starten, Webots-URL erhalten |
| Client → Webots-Instanz | WebSocket | 2001+ | Client → Server | Streaming, Zustandsdaten |
| Ext. Controller → Webots-Instanz | WebSocket | 2001+ | Extern → Container | Robotersteuerung |

---

## LAN-Erweiterung

> Für reinen **localhost-Zugriff** (Windows ↔ WSL2) ist keine zusätzliche
> Netzwerkkonfiguration nötig — WSL2 leitet `localhost`-Ports automatisch weiter.
> Die folgenden Schritte sind nur für den Zugriff **anderer Rechner im Netzwerk** erforderlich.

### Option A: WSL2 mirrored networking (empfohlen ab Windows 11 22H2)

Datei `C:\Users\<Windows-Benutzername>\.wslconfig` anlegen oder ergänzen:

```ini
[wsl2]
networkingMode=mirrored
```

Danach WSL2 neu starten:

```powershell
wsl --shutdown
```

WSL2 bekommt damit dieselbe IP-Adresse wie Windows — LAN-Clients erreichen die
Server direkt über die Windows-IP.

### Windows Firewall-Regeln

```powershell
# Als Administrator ausführen
New-NetFirewallRule -DisplayName "Webots Session Server" `
    -Direction Inbound -Protocol TCP -LocalPort 1999 -Action Allow
New-NetFirewallRule -DisplayName "Webots Simulation Ports" `
    -Direction Inbound -Protocol TCP -LocalPort 2000-2099 -Action Allow
```

### Option B: Port-Proxy (Fallback für älteres WSL2 oder NAT-Modus)

```powershell
$wslIp = (wsl hostname -I).Trim()

netsh interface portproxy add v4tov4 `
    listenport=1999 listenaddress=0.0.0.0 `
    connectport=1999 connectaddress=$wslIp

netsh interface portproxy add v4tov4 `
    listenport=2000 listenaddress=0.0.0.0 `
    connectport=2000 connectaddress=$wslIp
```

> Die WSL2-IP ändert sich bei jedem Neustart. Port-Proxies ggf. per Startup-Skript erneuern.

---

## Port Rewrite (für Produktionssetup mit SSL)

Für den produktiven Betrieb hinter einem Apache-Reverse-Proxy mit SSL müssen
`ssl: true` und `portRewrite: true` in beiden Konfigurationsdateien gesetzt werden.
Anfragen an Port 443 werden dann vom Webserver an die internen Ports weitergeleitet:

```text
wss://meinserver.de/2000/client  →  ws://localhost:2000/client
https://meinserver.de/2000/monitor  →  http://localhost:2000/monitor
```

Dafür in `/etc/apache2/sites-available/000-default-le-ssl.conf` eintragen:

```apache
RewriteEngine on
# WebSocket (zuerst)
RewriteCond %{HTTP:Upgrade} websocket [NC]
RewriteCond %{HTTP:Connection} upgrade [NC]
RewriteRule ^/(\d*)/(.*)$ "ws://localhost:$1/$2" [P,L]
# HTTP
RewriteRule ^/load$    "http://localhost:1999/load"    [P,L]
RewriteRule ^/monitor$ "http://localhost:1999/monitor" [P,L]
RewriteRule ^/session$ "http://localhost:1999/session" [P,L]
RewriteRule ^/(\d*)/(.*)$ "http://localhost:$1/$2" [P,L]
```

> Für lokale Entwicklung mit `portRewrite: false` und `ssl: false` ist kein Apache nötig.

---

## Häufige Probleme

| Problem | Ursache | Lösung |
| --- | --- | --- |
| `docker: permission denied` | Benutzer nicht in docker-Gruppe | `sudo usermod -aG docker $USER`, neu anmelden |
| Container startet, Webots hängt | Kein Display für WSLg | `DISPLAY`-Variable prüfen; `xhost +` auf Server ausführen |
| `requests.get("/session")` gibt Fehler zurück | Kein Simulation Server verfügbar | Simulation Server zuerst starten, Status via `/monitor` prüfen |
| Controller verbindet nicht | Falscher DEF-Name oder Port | `WEBOTS_CONTROLLER_URL` und `DEF`-Name in `.wbt` abgleichen |
| Session Server gibt 0 zurück | Keine freien Simulation Server | `maxConnections` erhöhen oder laufende Sessions beenden |
| Port nicht erreichbar von LAN | Firewall blockiert | Firewall-Regeln prüfen (Abschnitt LAN-Erweiterung) |
| `networkingMode=mirrored` fehlt | Windows-Version zu alt | Windows 11 22H2+ oder Port-Proxy-Fallback nutzen |
| pip-Installation schlägt fehl | Ubuntu 24.04 PEP 668 | Virtual Environment verwenden (Schritt 5) |
| Langer Timeout beim ersten Start | GitHub-Repo wird geklont | `ping_interval=None` in WebSocket-Connect setzen |
