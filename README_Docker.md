# Start Webots Simulation Server in Docker

1. Install WSL and Docker Desktop on your Windows machine.

``` Bash
# Install WSL
wsl --install -d Ubuntu:22.04
# Follow the prompts to complete the installation
```

2. Enable WSL integration with Docker Desktop.

``` Bash
# Open Docker Desktop settings
# Go to "Resources" > "WSL Integration"
# Enable integration for your WSL distribution (e.g., Ubuntu-22.04)
```

3. Open a PowerShell terminal and start the WSL distribution.

``` Bash 
# Start WSL distribution
wsl -d Ubuntu-22.04
```
4. Create a directory for the simulation server and navigate to it.

5. Create a `config` directory and add a `simulation.json` file with the desired simulation configuration. For example:

``` json
{
  "server": "localhost",
  "ssl": false,
  "portRewrite": false,
  "port": 2000,
  "docker": true,
  "debug": true,
  "webotsHome": "/usr/local/webots",
  "notify": []
}
```

6. In the WSL terminal, create a Docker-Compose with the following content:

``` yaml
services:
  simulation-server:
    build:
      context: .
      dockerfile_inline: |
        FROM ubuntu:22.04
        ENV DEBIAN_FRONTEND=noninteractive
        RUN apt-get update && apt-get install -y \
          python3 \
          python3-pip \
          git \
          curl \
          ca-certificates \
          && rm -rf /var/lib/apt/lists/*
        RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
          echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu jammy stable" \
          > /etc/apt/sources.list.d/docker.list && \
          apt-get update && apt-get install -y docker-ce-cli docker-compose-plugin && \
          rm -rf /var/lib/apt/lists/*
        WORKDIR /webots-server
        RUN git clone https://github.com/cyberbotics/webots-server.git . && \
          pip3 install pynvml requests psutil tornado distro websockets
        RUN sed -i "s|https://git@github.com/|https://github.com/|g" simulation_server.py
        EXPOSE 2000
        CMD ["python3", "/webots-server/simulation_server.py", "/config/simulation.json"]
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "2000:2000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - webots_projects:/projects
      - webots_logs:/logs
      - ./config/simulation.json:/config/simulation.json:ro
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
      - WEBOTS_HOME=/usr/local/webots
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:2000/load"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

volumes:
  webots_projects:
    driver: local
  webots_logs:
    driver: local
```

7. Save the file as `docker-compose.yml` and run the following command to start the simulation server:

``` Bash
docker compose up -d
```

8. The simulation server should now be running and accessible at `http://localhost:2000`. You can check the logs with:

``` Bash
docker compose logs -f
```

9. To stop the simulation server, run:

``` Bash
docker compose down
```

10. To start a new simulation, the world needs to be accessible in Github. You can create a new repository and push your world file there. Then, you can use the GitHub URL to load the world in the simulation server. For example:

Make sure you have `node-ws` installed to send the request to the simulation server.

You can use the following code snippet to load a world from GitHub:

``` Bash
# 1. Install node-ws if you haven't already
# 2. connect to the simulation server via WebSocket 
wscat -c ws://localhost:2000/client

# 3. Send a request to load the world from GitHub e.g.
{"start":{"url":"https://github.com/haecto/Webots_Test_World/blob/main/webots/worlds/ETrack.wbt","mode":"w3d"}}
```

A new Docker container will be created for the simulation, and you can access the simulation stream at `http://localhost:2001/index.html`. 

Port needs to be adapted to the one given in the simulation server logs. (e.g., `webots:ws://localhost:2001`)