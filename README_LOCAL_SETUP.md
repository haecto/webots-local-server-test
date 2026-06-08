# Webots Local Server Setup - Test Guide

## Struktur

```
webots-local-server-test/
├── config/
│   ├── simulation.json          # Server-Konfiguration
│   └── session.config.json      # Session-Server-Config
├── webots/                      # 🌍 Dein Webots-Projekt (lokal)
│   ├── worlds/
│   │   ├── SensorFusionTrack.wbt
│   │   └── ...
│   └── controllers/
├── docker-compose.yml           # Docker Setup
├── load_world.py               # Startup-Skript
└── requirements.txt             # Python-Dependencies
```

## Schnellstart

### 1. Docker-Compose starten
```bash
docker-compose up -d
```

Überprüfe den Status:
```bash
docker-compose ps
```

Healthcheck:
```bash
curl http://localhost:2000/load
```

### 2. Welt laden mit load_world.py

```bash
python load_world.py "https://github.com/cyberbotics/webots/blob/master/projects/objects/walls/worlds/wall.wbt"
```

Optionen:
```bash
# Mit mjpeg-Modus (statt w3d)
python load_world.py <url> --mode mjpeg

# Ohne Browser automatisch öffnen
python load_world.py <url> --no-browser

# Custom Server
python load_world.py <url> --server localhost:2000
```

### 3. Logs anschauen

```bash
# Simulation Server Logs
docker-compose logs simulation-server -f

# Webots Logs
docker volume inspect webots-local-server-test_webots_logs
```

## Was passiert intern?

1. **load_world.py** sendet WebSocket-Request an Simulation Server (`ws://localhost:2000/client`)
2. **Simulation Server** klont die GitHub-Welt und startet Webots in Docker
3. **Webots** streamet die Simulation über WebSocket (w3d oder mjpeg)
4. **Browser** zeigt die Welt an

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `Connection refused` | `docker-compose up -d` starten |
| `No webots URL in response` | Logs mit `docker-compose logs` prüfen |
| `GitHub clone failed` | GitHub-URL überprüfen und `allowedRepositories` anpassen |
| `GPU nicht verfügbar` | Docker NVIDIA-Runtime prüfen: `docker run --rm --runtime=nvidia nvidia-smi` |

## Test-Welten

```bash
# ✅ Lokale Welt aus DIESEM Repo
python load_world.py "https://github.com/haecto/webots-local-server-test/blob/main/webots/worlds/SensorFusionTrack.wbt"
python load_world.py "https://github.com/haecto/webots-local-server-test/blob/main/webots/worlds/PlatoonTrack.wbt"
python load_world.py "https://github.com/haecto/webots-local-server-test/blob/main/webots/worlds/LineFollowerTrack.wbt"

# ✅ Offizielle Webots Demo
python load_world.py "https://github.com/cyberbotics/webots/blob/master/projects/objects/walls/worlds/wall.wbt"
```

## Abhängigkeiten

Lokal brauchst du:
- Python 3.10+
- `websockets` (für load_world.py)

```bash
pip install websockets
```

Docker braucht:
- Docker + NVIDIA-Runtime
- NVIDIA GPU
