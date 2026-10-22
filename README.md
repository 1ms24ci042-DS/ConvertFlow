# ConvertFlow — DevOps assignment

**Dhanekula Sathwika · 1MS24CI042 · DevOps 25CIAEC59**

Repository: https://github.com/1ms24ci042-DS/ConvertFlow (private).

A stateless Java REST API for length, mass, and temperature conversion. Java 17 bytecode runs on JDK 17 or newer; the Ubuntu build uses OpenJDK 21 and bundled Maven 3.9.9. JUnit Jupiter 5.11.4 provides 15 automated tests.

## Build and API

```bash
mvn -B clean verify
java -jar target/convertflow.jar
curl http://localhost:8080/health
curl 'http://localhost:8080/convert?from=km&to=mi&value=5'
```

GET `/` gives metadata; `/health` returns `{"status":"UP"}`; `/convert` accepts lowercase units (m/km/mi/ft, kg/g/lb, c/f/k). Invalid requests return 400, unknown routes 404, and unsupported methods 405. `APP_PORT` sets the listening port. The health endpoint is not a Prometheus metrics endpoint.

## Verified Ubuntu deployment

Fresh execution logs are in `evidence/live/`. The older top-level evidence files and old rendered log images came from the supplied workspace and are not used to establish Ubuntu results. `evidence/PROVENANCE.md` explains the evidence sources.

- Maven clean verify: 15 tests, zero failures/errors/skips.
- Ansible role: first run changed six tasks; second run changed zero, with zero failures. Service `convertflow` runs as an unprivileged user from `/opt/convertflow`.
- Docker: multi-stage image `convertflow:1.0.0`, non-root UID/GID 10001, working health and conversion endpoints.
- Kind v0.27.0, Kubernetes v1.32.2, kubectl v1.32.2: actual scaling 3 -> 5 -> 3, with every recorded Pod Ready and no terminating Pods at each observation.
- ConfigMap injects APP_PORT=8080; readiness and liveness probes use `/health`; Service and Deployment selectors match `app=convertflow`.

The laptop keeps the systemd app on **8080**, Docker on **8081**, Jenkins on **8082**, and Kubernetes Service forwarding on **8083** so the demonstrations coexist. Port-forward is an active process and must be restarted after reboot:

```bash
kubectl --context kind-convertflow port-forward --address 127.0.0.1 service/convertflow 8083:8080
```

## Jenkins Pipeline from SCM

Job: http://localhost:8082/job/ConvertFlow/

The job uses the private GitHub repository, branch `*/main`, script `Jenkinsfile`, and a Linux executor labelled `linux`. Pipeline, Git, JUnit and Timestamper plugins are installed. Maven 3.9.9 is on the executor PATH. GitHub access is stored encrypted by Jenkins; no token is part of this repository. The existing administrator secret remains local to Jenkins.

The Jenkinsfile polls SCM every two minutes (`H/2 * * * *`). The Test stage gates Package; post-build actions publish JUnit results and archive/fingerprint `target/convertflow.jar`. The first build establishes the polling baseline; subsequent pushed commits are discovered by the scheduler. `evidence/live/jenkins-*` records actual build causes, commits, console output, test results and archive metadata.

## Ansible and cluster reproduction

Review `scripts/setup-ubuntu.sh` and run with Bash if the Ubuntu tools are absent. Docker group membership is privileged; the script explicitly adds the desktop user to that group.

```bash
bash scripts/deploy-ubuntu.sh
bash scripts/deploy-kind.sh
```

The Ubuntu script requests sudo locally, checks port ownership, stops only the known manual JAR if needed, and runs Ansible twice. The role installs Java, creates the service user and directory, copies the built JAR, templates the systemd unit, and notifies a restart handler when files change. A repeat run checks idempotence and health.

The cluster script builds the image, reuses or creates `convertflow`, loads the image, applies the ConfigMap/Deployment/Service, and verifies exact Ready Pod counts at 3, 5, and 3. It pins the node version to match kubectl. It retains the cluster and writes real generated logs. No database or PVC is needed for this stateless API. Scaling is manual, not autoscaling.

## Report and submission

The institutional template is preserved as `report/original_template.tex`. Final reports and the submission archive are under `submission/`; `report/main.tex` is the personalized source. Both components contain their own Abstract, Introduction, Implementation, Enhancement, Results, Conclusion and References. Figures are actual browser screenshots of Jenkins, application responses, or fresh log files, with their origin stated in captions. No terminal image is synthesized. Signature and marks fields remain blank. No collaborator is invited, per the student's instruction.

Keep the working services and cluster for the demo. Cleanup is intentionally deferred.
