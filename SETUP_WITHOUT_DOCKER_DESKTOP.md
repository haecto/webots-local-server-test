# Setting Up Docker Engine in WSL2 (Without Docker Desktop)

This guide replaces the "Set up Docker Desktop" step from the main README.
All commands are run inside the WSL2 shell.

---

## Step 1: Install Docker Engine

```bash
# Prerequisites
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
sudo tee /etc/apt/sources.list.d/docker.list

# Refresh package lists and install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

---

## Step 2: Add User to Docker Group

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## Step 3: Start Docker Daemon and Test

```bash
sudo service docker start
docker run --rm hello-world
```

> WSL2 does not run systemd by default. The daemon must be started manually after each
> WSL2 restart using `sudo service docker start`, or automated via `.bashrc` (see below).

### Optional: Auto-start Docker on WSL2 Launch

Add to the end of `~/.bashrc`:

```bash
if [ "$(sudo service docker status 2>&1)" != " * Docker is running" ]; then
    sudo service docker start > /dev/null 2>&1
fi
```

To allow `sudo service docker start` without a password prompt, add via `sudo visudo`:

```
%docker ALL=(ALL) NOPASSWD: /usr/sbin/service docker *
```

---

## Step 4: Install NVIDIA Container Toolkit

Required for Docker containers to access the Windows host GPU:

```bash
# GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Repository with correct signed-by entry
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt update && sudo apt install -y nvidia-container-toolkit

# Configure Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo service docker restart
```

---

## Step 5: Verify GPU Access

```bash
# GPU directly in WSL2
nvidia-smi

# GPU inside a Docker container
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi
```

Both commands should display the GPU name, driver version, and CUDA version.

---

## Troubleshooting

| Problem | Cause | Solution |
| --- | --- | --- |
| `docker-ce` not found | `apt update` not run after adding the Docker repo | Run `sudo apt update` again after the `echo` command |
| GPG error on NVIDIA repo | `signed-by` missing from the `.list` file | Delete the repo file and recreate it using the `sed` command in Step 4 |
| `docker: permission denied` | User not in docker group or group not yet active | Run `newgrp docker` or log out and back in |
| Docker daemon not running | WSL2 restarted without starting Docker | Run `sudo service docker start` |
| CUDA image not found | Wrong image tag | Check available tags on Docker Hub, e.g. `12.3.1-base-ubuntu22.04` |
