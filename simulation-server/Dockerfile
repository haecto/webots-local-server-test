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
  pip3 install pynvml requests psutil tornado distro websockets && \
  sed -i "s|https://git@github.com/|https://github.com/|g" simulation_server.py && \
  echo 'RUN apt-get update && apt-get install -y mosquitto-clients && rm -rf /var/lib/apt/lists/*' \
  >> /webots-server/config/simulation/docker/Dockerfile.default && \
  printf '\nnetworks:\n  default:\n    external: true\n    name: webots-local-server-test_default\n' \
  >> /webots-server/config/simulation/docker/docker-compose-default.yml
EXPOSE 2000
CMD ["python3", "/webots-server/simulation_server.py", "/config/simulation.json"]