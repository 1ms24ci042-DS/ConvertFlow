#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence/generated
docker build -t convertflow:1.0.0 . 2>&1 | tee evidence/generated/docker-build.txt
if ! kind get clusters | grep -qx convertflow; then kind create cluster --name convertflow; fi
kind load docker-image convertflow:1.0.0 --name convertflow
kubectl --context kind-convertflow apply -f k8s/deployment.yaml
kubectl --context kind-convertflow rollout status deployment/convertflow --timeout=180s
kubectl --context kind-convertflow get pods -l app=convertflow -o wide | tee evidence/generated/pods-3.txt
kubectl --context kind-convertflow scale deployment/convertflow --replicas=5
kubectl --context kind-convertflow rollout status deployment/convertflow --timeout=180s
kubectl --context kind-convertflow get pods -l app=convertflow -o wide | tee evidence/generated/pods-5.txt
kubectl --context kind-convertflow scale deployment/convertflow --replicas=3
kubectl --context kind-convertflow rollout status deployment/convertflow --timeout=180s
kubectl --context kind-convertflow get pods -l app=convertflow -o wide | tee evidence/generated/pods-down-3.txt
kubectl --context kind-convertflow get svc convertflow | tee evidence/generated/service.txt
kubectl --context kind-convertflow get configmap convertflow-config -o yaml | tee evidence/generated/configmap.txt
kubectl --context kind-convertflow get deployment convertflow -o yaml > evidence/generated/deployment-live.yaml
echo 'Now run: kubectl --context kind-convertflow port-forward service/convertflow 8081:8080'
echo 'Then: curl "http://localhost:8081/convert?from=km&to=mi&value=5"'
