#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence/live
sudo -v
# Release only the verified manually launched ConvertFlow process on 8080.
if ! systemctl is-active --quiet convertflow; then
  pid=$(ss -ltnp 'sport = :8080' | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1)
  if [[ -n "$pid" ]]; then
    args=$(ps -p "$pid" -o args=)
    if [[ "$args" == 'java -jar target/convertflow.jar' ]]; then
      printf 'Stopping manual ConvertFlow PID %s before systemd deployment\n' "$pid"
      kill -TERM "$pid"
      sleep 2
    else
      printf 'Port 8080 belongs to an unexpected process: %s\n' "$args"
      exit 1
    fi
  fi
fi
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml 2>&1 | tee evidence/live/ansible-first.txt
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml 2>&1 | tee evidence/live/ansible-second.txt
systemctl status convertflow --no-pager | tee evidence/live/systemd-status.txt
curl -fsS http://127.0.0.1:8080/health | tee evidence/live/systemd-health.json
read -r -p 'Deployment finished. Press Enter to close. '
