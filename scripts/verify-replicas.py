"""Verify the exact live ready Pod count after a Kubernetes scaling operation."""
import json
import os
import subprocess
import time

expected = int(os.environ["EXPECTED_REPLICAS"])
for attempt in range(90):
    output = subprocess.check_output([
        "kubectl", "--context", "kind-convertflow", "get", "pods",
        "-l", "app=convertflow", "-o", "json",
    ])
    pods = json.loads(output)["items"]
    ready = [p for p in pods if not p["metadata"].get("deletionTimestamp")
             and any(c["type"] == "Ready" and c["status"] == "True"
                     for c in p.get("status", {}).get("conditions", []))]
    if len(pods) == expected and len(ready) == expected:
        print(f"Verified {expected} Pods, all Ready, none terminating", flush=True)
        break
    time.sleep(2)
else:
    raise SystemExit(f"Expected {expected} ready Pods; observed {len(pods)} total, {len(ready)} ready")
