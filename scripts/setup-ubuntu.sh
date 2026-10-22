#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence/live
# Privileged actions: install free Ubuntu tools, enable Docker, add the current
# desktop user to Docker's privileged group. No credentials are saved.
sudo apt-get update
sudo apt-get install -y gh docker.io ansible-core maven python3-venv python3-reportlab python3-docx gnome-screenshot
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
printf '\nSetup complete. Return to Codex; no logout is needed for sg docker commands.\n'
read -r -p 'Press Enter to close this window. '
