# Verified completion checklist — Ubuntu, 22 October 2026

- [x] Maven clean verify: 15 tests, zero failures/errors/skips.
- [x] Private GitHub repository https://github.com/1ms24ci042-DS/ConvertFlow; main and feature branch pushed; original merge retained.
- [x] Jenkins Pipeline from SCM, Linux label, Maven 3.9.9 PATH, Pipeline/Git/JUnit/Timestamper plugins.
- [x] Initial Jenkins build #1 succeeded; SCM polling automatically triggered build #2 after pushed commit bb4ffa7.
- [x] Automatic build #2: 15 tests passed, JUnit report published, JAR archived and downloaded for SHA-256 verification.
- [x] Supplementary GitHub Actions runs succeeded; Jenkins independently verified.
- [x] Ansible role/variables/handler/systemd deployment: first changed=6; second changed=0; both failed=0.
- [x] Docker multi-stage build, non-root running container, real health and conversion responses on 8081.
- [x] Kind Kubernetes deployment, Service access on 8083, ready endpoints and health/conversion responses.
- [x] Actual 3 -> 5 -> 3 scaling; every observation has exact Ready Pod count with no terminating Pods.
- [x] ConfigMap injection, health probe configuration, matching labels/selectors, resource/security settings inspected live.
- [x] Genuine browser screenshots of Jenkins, API responses and fresh logs; no synthesized terminal screenshots.
- [x] Institutional report has separate complete Component 1 and Component 2 sections; signatures and marks blank.
- [x] Final PDF/DOCX generation and PDF visual review; final ZIP manifest is recorded under submission/.

No collaborator invitation: student explicitly requested that it was not needed. No separate assignment PDF was found; the supplied institutional LaTeX template contains the requirements/rubrics. Historical supplied evidence is preserved but excluded from the new clean submission; see PROVENANCE.md.
