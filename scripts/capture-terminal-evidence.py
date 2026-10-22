#!/usr/bin/env python3
"""Execute evidence commands in GNOME Terminal and capture its real window.

Images come exclusively from gnome-screenshot. Historical log review is explicitly
labelled; all other recipes execute fresh checks. No terminal image is rendered.
"""
from pathlib import Path
import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/terminal'
SHOTS = ROOT / 'report/screenshots'
EVIDENCE.mkdir(exist_ok=True)
recipes = {
    'git': ["git log --graph --all --format='%h %s' -8", 'git branch -a'],
    'ansible-first-history': [
        "printf 'HISTORICAL LOG: first deployment, 22 October 2026\nNot a new first run. Original file and handler output follow.\n'",
        "stat -c '%y %n' evidence/live/ansible-first.txt",
        'tail -n 18 evidence/live/ansible-first.txt',
    ],
    'ansible-repeat': [
        'sudo -v',
        'ansible-playbook -i ansible/inventory.ini ansible/playbook.yml > evidence/terminal/ansible-repeat.txt 2>&1',
        'tail -n 18 evidence/terminal/ansible-repeat.txt',
    ],
    'ansible-idempotent': [
        'sudo -v',
        'ansible-playbook -i ansible/inventory.ini ansible/playbook.yml > evidence/terminal/ansible-idempotent.txt 2>&1',
        'tail -n 18 evidence/terminal/ansible-idempotent.txt',
    ],
    'systemd': [
        'systemctl --no-pager status convertflow | head -n 10',
        "curl -fsS http://127.0.0.1:8080/health; printf '\n'",
    ],
    'maven': [
        'mvn -B -ntp clean verify > evidence/terminal/maven-build.txt 2>&1',
        'tail -n 15 evidence/terminal/maven-build.txt',
    ],
    'docker-build': [
        "sg docker -c 'docker build -t convertflow:1.0.0 .' > evidence/terminal/docker-build.txt 2>&1",
        'tail -n 12 evidence/terminal/docker-build.txt',
    ],
    'docker-runtime': [
        "sg docker -c 'docker ps --filter name=convertflow-demo --format \"table {{.Names}}\\t{{.Image}}\\t{{.Status}}\"'",
        "sg docker -c 'docker exec convertflow-demo id'",
        "curl -fsS http://127.0.0.1:8081/health; printf '\n'",
        "curl -fsS 'http://127.0.0.1:8081/convert?from=km&to=mi&value=5'; printf '\n'",
    ],
    'kubernetes-3': [
        'EXPECTED_REPLICAS=3 python3 scripts/verify-replicas.py',
        'kubectl --context kind-convertflow get pods -l app=convertflow',
        'kubectl --context kind-convertflow get rs -l app=convertflow',
    ],
    'kubernetes-5': [
        'kubectl --context kind-convertflow scale deployment/convertflow --replicas=5',
        'EXPECTED_REPLICAS=5 python3 scripts/verify-replicas.py',
        'kubectl --context kind-convertflow get pods -l app=convertflow',
    ],
    'kubernetes-down-3': [
        'kubectl --context kind-convertflow scale deployment/convertflow --replicas=3',
        'EXPECTED_REPLICAS=3 python3 scripts/verify-replicas.py',
        'kubectl --context kind-convertflow get pods -l app=convertflow',
    ],
    'kubernetes-service': [
        'kubectl --context kind-convertflow get svc convertflow',
        "curl -fsS http://127.0.0.1:8083/health; printf '\n'",
        "curl -fsS 'http://127.0.0.1:8083/convert?from=km&to=mi&value=5'; printf '\n'",
    ],
    'kubernetes-config': [
        "kubectl --context kind-convertflow get cm convertflow-config -o jsonpath='{.data}'; printf '\n'",
        'kubectl --context kind-convertflow exec deployment/convertflow -- printenv APP_PORT',
    ],
    'kubernetes-probes': [
        "kubectl --context kind-convertflow describe deployment convertflow | sed -n '/    Liveness:/,/    Environment:/p'",
        'kubectl --context kind-convertflow get deployment convertflow',
    ],
}
name = sys.argv[1]
commands = recipes[name]
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
temp = Path('/tmp') / f'convertflow-capture-{name}-{stamp}'
temp.mkdir()
shot = SHOTS / f'terminal-{name}.png'
done, failed = temp / 'done', temp / 'failed'
ready = temp / 'ready'
rc = temp / 'bashrc'
maven = ROOT.parents[1] / 'work/tools/maven/apache-maven-3.9.9/bin'
# ROOT.parents[1] is i-x20, containing the existing dependency cache.
cache = ROOT.parents[1] / 'work/m2'
rc.write_text("PS1='\\u:\\W\\$ '\n"
              + 'while [[ ! -f ' + shlex.quote(str(ready)) + ' ]]; do sleep 0.1; done\n'
              + 'cd ' + shlex.quote(str(ROOT)) + '\n'
              + 'export PATH=' + shlex.quote(str(Path.home() / '.local/bin') + ':' + str(maven)) + ':"$PATH"\n'
              + 'export MAVEN_OPTS=' + shlex.quote('-Dmaven.repo.local=' + str(cache)) + '\n'
              + "trap 'touch " + shlex.quote(str(failed)) + "' ERR\nset -eE -o pipefail\nclear\nset -x\ndate -Iseconds\n"
              + '\n'.join(commands) + '\nset +x\n'
              + '(sleep 3; gnome-screenshot -w -f ' + shlex.quote(str(shot))
              + ' > ' + shlex.quote(str(temp / 'capture-output.txt')) + ' 2>&1 && touch '
              + shlex.quote(str(done)) + ' || touch ' + shlex.quote(str(failed)) + ') &\n')
transcript = temp / 'session.typescript'
def windows():
    output = subprocess.check_output(['busctl', '--user', 'tree', 'org.gnome.Terminal'], text=True)
    return set(re.findall(r'/org/gnome/Terminal/window/\d+', output))

before = windows()
subprocess.run([
    'gnome-terminal', '--window', '--geometry=84x28', '--zoom=1.3',
    '--title=ConvertFlow evidence: ' + name, '--working-directory=' + str(ROOT),
    '--', 'script', '-q', '-f', str(transcript), '-c',
    'bash --noprofile --rcfile ' + shlex.quote(str(rc)) + ' -i',
], check=True)
target = None
for _ in range(30):
    added = windows() - before
    if added:
        target = sorted(added)[-1]
        break
    time.sleep(0.1)
if target:
    subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.gnome.Terminal',
                    '--object-path', target, '--method', 'org.gtk.Actions.Activate',
                    'size-to', '[<(uint32 84, uint32 28)>]', '{}'], check=True,
                   stdout=subprocess.DEVNULL)
    time.sleep(0.5)
ready.touch()
for _ in range(600):
    if failed.exists():
        raise SystemExit(f'Terminal command/capture failed. Inspect {transcript}')
    if done.exists():
        break
    time.sleep(1)
else:
    raise SystemExit(f'Terminal session pending, possibly local sudo prompt: {transcript}')
shutil.copyfile(transcript, EVIDENCE / (name + '.typescript'))
metadata = {'name': name, 'commands': ['date -Iseconds'] + commands,
            'historical_log_review': name == 'ansible-first-history',
            'captured_at': datetime.datetime.now().astimezone().isoformat(),
            'screenshot': shot.relative_to(ROOT).as_posix(),
            'method': 'gnome-screenshot --window; real GNOME Terminal with Bash xtrace and prompt'}
metadata['window_object'] = target
(EVIDENCE / (name + '.json')).write_text(json.dumps(metadata, indent=2) + '\n')
print('Captured actual terminal:', name, flush=True)
