# ConvertFlow - DevOps project

**Dhanekula Sathwika | 1MS24CI042 | 25CIAEC59**

A stateless Java 17 REST API demonstrating a Maven/Jenkins CI pipeline, Ansible server configuration, and Docker/Kubernetes deployment. No database or external runtime libraries are required.

## Run the application

Install JDK 17+ and Maven 3.9+, then run from this directory:

```sh
mvn clean verify
java -jar target/convertflow.jar
curl http://localhost:8080/health
curl 'http://localhost:8080/convert?from=km&to=mi&value=5'
```

Routes: GET `/` (metadata), `/health` (health), `/convert?from=UNIT&to=UNIT&value=NUMBER` (conversion). Units: length m/km/mi/ft; mass kg/g/lb; temperature c/f/k. Invalid input returns HTTP 400, unknown routes 404, unsupported methods 405. APP_PORT configures the listening port. Unit names are lowercase. Health is a JSON status endpoint, not a Prometheus metrics endpoint.

## Git and hosting

The supplied local repository contains a main branch and a retained feature branch with a real merge commit. Publish using your own GitHub/GitLab account: create an empty repository, add its URL as origin, then `git push -u origin main` and `git push origin feature/conversion-api`. Update repo_link.txt and the report with that actual URL. Add the course coordinator as collaborator using their correct account; no account has been guessed.

## Jenkins

Use a Linux Jenkins agent labelled `linux` with Git, JDK 17, Maven 3.9+ on PATH. Install Pipeline, Git, JUnit, and Timestamper plugins. Create Pipeline from SCM, select Git, enter your published repository URL, choose branch `*/main`, script path `Jenkinsfile`. Run once to establish SCM polling. The Jenkinsfile checks for changes every two minutes, runs tests, packages the JAR only after tests pass, publishes JUnit results, and archives target/convertflow.jar. Push a subsequent change and capture the automatic run. A Jenkinsfile alone is not evidence that a job ran. GitHub Actions is supplementary and does not replace required Jenkins evidence.

## Ansible

Use an Ubuntu VM or WSL Ubuntu with systemd enabled. Install ansible-core; build the JAR first. From `ansible/`:

```sh
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
curl http://localhost:8080/health
```

The second playbook run should report no configuration changes. The role installs Java, creates an unprivileged service account, copies the JAR, templates a systemd unit, and uses a restart handler only when files change. Inventory defaults to the local Linux control node. To use a remote Ubuntu VM, replace localhost with its actual SSH inventory and build/copy from the control node. This playbook is for a systemd host; an ordinary Docker container is not a substitute.

## Docker and Kubernetes

Install Docker, Kind, kubectl and Bash on the deployment host. With Docker running:

```sh
docker build -t convertflow:1.0.0 .
docker run --rm -p 8081:8080 convertflow:1.0.0
# In another terminal: curl http://localhost:8081/health
# Stop that container before port-forwarding below.
bash scripts/deploy-kind.sh
kubectl --context kind-convertflow port-forward service/convertflow 8081:8080
# In another terminal:
curl 'http://localhost:8081/convert?from=km&to=mi&value=5'
```

The script creates a named cluster, loads the local image, applies the ConfigMap/Deployment/Service, and records scaling 3 -> 5 -> 3. It does not delete an existing cluster. Kind NodePort access differs by host, so port-forward is the documented Windows-compatible access path. Use `kubectl --context kind-convertflow get rs -l app=convertflow` to show the ReplicaSet. Readiness controls routing eligibility; liveness restarts an unhealthy container. The Docker image uses a build stage and a non-root runtime. APP_PORT and the container/probe/service ports must stay consistent if changed.

## Report and evidence

The report uses the supplied institutional structure. Local build/test evidence is included where actually obtained. Jenkins, Docker, Ansible and Kubernetes results must be captured on a running environment; no successful deployment or fabricated screenshot is claimed. Add screenshots listed in evidence/CHECKLIST.md, enter the final repository URL, and obtain required signatures before submission. The certificate signature lines are intentionally blank.

## Cleanup (only after your demo)

`kind delete cluster --name convertflow` removes the demo cluster. On the Ansible host, stop/disable the service with `sudo systemctl disable --now convertflow` if no longer needed.
