# Required evidence coverage

| # | Required evidence | Report figure(s) | Status |
|---|---|---|---|
| 1 | Git branches and merge | 1 | Verified |
| 2 | Maven build and 15-test total | 2 | Verified |
| 3 | Jenkins Pipeline from SCM | 3 | Verified |
| 4 | Repository and main branch without credential values | 4, 5 | Verified |
| 5 | Automatic SCM polling configuration | 6 | Verified |
| 6 | Successful automatic build cause and revision | 7 | Verified |
| 7 | Published JUnit results | 8 | Verified |
| 8 | Archived JAR and successful console | 7, 9 | Verified |
| 9 | Historical Ansible first run and handler | 10 | Verified |
| 10 | Fresh Ansible idempotence (changed=0) | 12 | Verified |
| 11 | Active systemd service and health | 13 | Verified |
| 12 | Docker image build, container and API | 14, 15 | Verified |
| 13 | Three Ready Kubernetes Pods | 16 | Verified |
| 14 | Scale to five Ready Pods | 17 | Verified |
| 15 | Scale back to exactly three Ready Pods | 18 | Verified |
| 16 | Kubernetes Service and working API | 19 | Verified |
| 17 | ConfigMap injection and readiness/liveness probes | 20, 21 | Verified |

Figure 11 additionally preserves the genuine rebuilt-JAR refresh (changed=2). Figure 10 is explicitly historical first-run log review in a real terminal; figures 11 and 12 are new playbook executions. Figures 3–9 are genuine Jenkins browser UI; all other figures are genuine GNOME Terminal window captures. The deployment remains at three Ready replicas.
