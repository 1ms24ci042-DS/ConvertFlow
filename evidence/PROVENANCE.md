# Evidence provenance and report correction

The current report has 21 figures: fourteen genuine GNOME Terminal window captures and seven genuine Jenkins browser UI captures. All command figures are captured directly by `gnome-screenshot --window`, with a real Bash session and xtrace showing executed commands. The tool does not draw text, a terminal frame or output into any image. The terminal session transcripts and capture timestamps are in `evidence/terminal/`; recipes are in `scripts/capture-terminal-evidence.py`.

## Historical evidence, preserved

The first Ubuntu Ansible deployment occurred on 22 October 2026 at approximately 20:26 IST. `live/ansible-first.txt` records changed=6 and handler execution, followed by `live/ansible-second.txt` with changed=0. The first-run figure is a real terminal displaying that preserved transcript and its original file timestamp. It explicitly says HISTORICAL LOG; it is not represented as a new first run.

Jenkins build #2 started on 22 October 2026 at 20:35:09 IST (15:05:09 UTC), completed SUCCESS, and records `hudson.triggers.SCMTrigger$SCMTriggerCause` and revision bb4ffa7bd2b27d05dd86a60d867639fa87f4a539. Its original genuine Jenkins UI figures and downloaded archived JAR are retained. The current Jenkins API was checked again; the successful automatic cause is preserved. No new manual build is labelled automatic.

## Fresh terminal verification

Git history, Maven clean verify, Docker build/runtime, systemd health, Service access, ConfigMap injection and probes were checked in actual Ubuntu terminals. A fresh scaling sequence verified exactly 3 -> 5 -> 3 Ready Pods, with no terminating Pods at each checkpoint. Capture JSON timestamps distinguish these checks from the historical deployment.

A fresh Ansible check initially returned changed=0. Maven subsequently rebuilt the JAR. A later Ansible run legitimately copied that rebuilt artifact and restarted the service, yielding changed=2; it is retained as the artifact-refresh result. The next unchanged run returned ok=8, changed=0, failed=0, with no restart handler. The role configuration was not modified to manufacture change output. `ansible-refresh.*` preserves the artifact-refresh capture originally named ansible-repeat; `ansible-idempotent.*` records the final unchanged run.

## Superseded and excluded material

The prior report used browser views of raw command logs. Those files remain in Git history and the working directory, but unreferenced screenshot files are filtered out of the new clean ZIP and are not used in either report. Initial captures that caught the Codex window were rejected and replaced before report generation. The top-level older Windows logs and rendered log illustrations remain untouched and are excluded from the current reports and selected submission files. The original full submission is backed up in submission/previous-* and is excluded from the new ZIP.

No separate original assignment PDF was found locally. `report/original_template.tex` supplies the component requirements and assessment rubrics. It requests real terminal output screenshots and contains no separate AI-assistance declaration to preserve; no institutional policy or declaration has been invented. Required signatures and evaluator marks remain blank. No coordinator invitation is made, as requested.
