#!/usr/bin/env python3
"""Generate institutional PDF, DOCX and LaTeX from verified live evidence.

Requires reportlab, python-docx and Pillow. Never creates evidence images.
"""
from pathlib import Path
import html
import json
import re
import textwrap
import os
import time
from datetime import datetime

# Use an unambiguous real UTC creation timestamp in generated PDF metadata.
os.environ['TZ'] = 'UTC'
time.tzset()

from PIL import Image as PILImage
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate,
    Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted, Image, KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'
OUT = ROOT / 'submission'
OUT.mkdir(exist_ok=True)
facts = json.loads((ROOT / 'evidence/live/verified-facts.json').read_text())
assert facts['passed_tests'] == 15
original = (REPORT / 'original_template.tex').read_text()
front = (REPORT / 'main.tex').read_text().split('\\section*{Component 1:', 1)[0]
if '\\usepackage{pdflscape}' not in front:
    front = front.replace('\\begin{document}', '\\usepackage{pdflscape}\n\\begin{document}')
tex = [front]
story = []
document = Document()
section = document.sections[0]
section.page_width, section.page_height = Inches(8.2677), Inches(11.6929)
section.top_margin = section.bottom_margin = Inches(0.8)
section.left_margin = section.right_margin = Inches(1)
normal = document.styles['Normal']
normal.font.name, normal.font.size = 'Times New Roman', Pt(12)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal.paragraph_format.space_after = Pt(8)
normal.paragraph_format.line_spacing = 1.1
normal.paragraph_format.keep_together = True
for name, size in [('Title', 18), ('Heading 1', 18), ('Heading 2', 16), ('Heading 3', 14)]:
    document.styles[name].font.name = 'Times New Roman'
    document.styles[name].font.size = Pt(size)
    document.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    document.styles[name].paragraph_format.space_before = Pt(10)
    document.styles[name].paragraph_format.space_after = Pt(8)
    document.styles[name].paragraph_format.keep_with_next = True
for style_name in ['Normal', 'Title', 'Heading 1', 'Heading 2', 'Heading 3', 'Footer']:
    st = document.styles[style_name]
    st.font.name = 'Times New Roman'
    st.font.color.rgb = RGBColor(0, 0, 0)
    fonts = st.element.get_or_add_rPr().get_or_add_rFonts()
    for key in list(fonts.attrib):
        if key.endswith('Theme'):
            del fonts.attrib[key]
document.styles['Footer'].font.size = Pt(12)
styles = getSampleStyleSheet()
for name, font, size, leading in [
    ('BodyReport', 'Times-Roman', 12, 16),
    ('HReport', 'Times-Bold', 18, 22),
    ('SubReport', 'Times-Bold', 16, 20),
    ('MinorReport', 'Times-Bold', 14, 18),
    ('CodeReport', 'Courier', 12, 14.5),
]:
    styles.add(ParagraphStyle(name=name, fontName=font, fontSize=size,
                             leading=leading, textColor=colors.black,
                             spaceBefore=8 if name != 'BodyReport' else 0,
                             spaceAfter=9, keepWithNext=name in ['HReport', 'SubReport', 'MinorReport']))
styles.add(ParagraphStyle(name='CenterReport', parent=styles['BodyReport'], alignment=1))
styles.add(ParagraphStyle(name='CellReport', parent=styles['BodyReport'], leading=14, spaceAfter=0))


def paragraph(text, style='BodyReport'):
    return Paragraph(html.escape(text).replace('\n', '<br/>'), styles[style])


def escape(text):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
               '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}'}
    return ''.join(mapping.get(c, c) for c in text)


evidence_mode = False
front_page_count = 0


def doc_section(wide=False):
    sec = document.add_section(WD_SECTION_START.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE if wide else WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = (Inches(11.6929), Inches(8.2677)) if wide else (Inches(8.2677), Inches(11.6929))
    sec.left_margin = sec.right_margin = Inches(1)
    sec.top_margin = sec.bottom_margin = Inches(0.8)
    for node in list(sec._sectPr.findall(qn('w:pgNumType'))):
        sec._sectPr.remove(node)
    return sec


def ensure_body():
    global evidence_mode
    if evidence_mode:
        story.extend([NextPageTemplate('Body'), PageBreak()])
        doc_section(False)
        evidence_mode = False


def body(text):
    ensure_body()
    story.append(paragraph(text))
    document.add_paragraph(text)
    tex.append(escape(text) + '\n\n')


def heading(text, level=1):
    ensure_body()
    story.append(paragraph(text, {1: 'HReport', 2: 'SubReport', 3: 'MinorReport'}[level]))
    document.add_heading(text, level=level)
    tex.append({1: '\\section*{', 2: '\\subsection*{', 3: '\\subsubsection*{'}[level] + escape(text) + '}\n')


def page(frontmatter=False):
    global front_page_count
    ensure_body()
    story.append(PageBreak())
    if frontmatter:
        front_page_count += 1
    if frontmatter and front_page_count == 2:
        sec = doc_section(False)
        num = OxmlElement('w:pgNumType'); num.set(qn('w:start'), '1'); sec._sectPr.append(num)
        sec.footer.is_linked_to_previous = False
        p = sec.footer.paragraphs[0]; p.alignment = 1
        fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); p._p.append(fld)
    else:
        document.add_page_break()
    if not frontmatter:
        tex.append('\\newpage\n')


def table(rows, widths):
    t = Table([[paragraph(str(c), 'CellReport') for c in row] for row in rows],
              colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(t)
    dt = document.add_table(rows=0, cols=len(rows[0]))
    dt.style = 'Table Grid'
    dt.autofit = False
    for column, width in zip(dt.columns, widths):
        column.width = Pt(width)
    for row in rows:
        dr = dt.add_row()
        dr._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell, value, width in zip(dr.cells, row, widths):
            cell.width = Pt(width)
            cell.text = str(value)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for run in p.runs:
                    run.font.name = 'Times New Roman'; run.font.size = Pt(12)


figure_number = 0
figures_used = []


def figure(name, caption):
    global figure_number, evidence_mode
    figure_number += 1
    path = REPORT / 'screenshots' / (name + '.png')
    assert path.is_file(), path
    figures_used.append(path.relative_to(ROOT).as_posix())
    im = PILImage.open(path)
    # A4 landscape evidence pages preserve readable terminal text and UI detail.
    if not evidence_mode:
        story.extend([NextPageTemplate('Evidence'), PageBreak()])
        doc_section(True)
    else:
        story.append(PageBreak())
        document.add_page_break()
    evidence_mode = True
    width = landscape(A4)[0] - 144
    height = width * im.height / im.width
    if height > 398:
        width *= 398 / height
        height = 398
    text = f'Figure {figure_number}. {caption}'
    if name.startswith('terminal-'):
        capture = json.loads((ROOT / 'evidence/terminal' / (name[9:] + '.json')).read_text())
        text += ' Captured ' + datetime.fromisoformat(capture['captured_at']).strftime('%d %b %Y, %H:%M:%S %z') + '.'
    story.append(KeepTogether([Image(str(path), width=width, height=height), paragraph(text)]))
    document.add_picture(str(path), width=Inches(width / 72))
    document.paragraphs[-1].paragraph_format.keep_with_next = True
    document.add_paragraph(text)
    document.paragraphs[-1].paragraph_format.keep_together = True
    tex.append('\\clearpage\\begin{landscape}\\begin{center}\\includegraphics[width=\\linewidth,height=0.78\\textheight,keepaspectratio]{screenshots/' + name + '.png}\\end{center}\n' + escape(text) + '\n\\end{landscape}\n')


def code(file, first=None, last=None):
    content = (ROOT / file).read_text().splitlines()
    if first is not None:
        content = content[first - 1:last]
    label = file + (f' (excerpt, lines {first}-{last})' if first else '')
    body(label)
    wrapped = '\n'.join('\n'.join(textwrap.wrap(line, 61, replace_whitespace=False,
                          drop_whitespace=False)) if line else '' for line in content)
    story.append(Preformatted(wrapped, styles['CodeReport']))
    for line in content:
        p = document.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line)
        r.font.name, r.font.size = 'Courier New', Pt(12)
    opts = f'[firstline={first},lastline={last}]' if first else ''
    tex.append('\\lstinputlisting' + opts + '{../' + file + '}\n')


def refs(items):
    start = len(story)
    heading('References', 2)
    for title, url in items:
        body(title + ': ' + url + ' (accessed 22 October 2026).')
    story[start:] = [KeepTogether(story[start:])]


# Reproduce the supplied institutional front matter, rubric and blank marks.
story.append(Spacer(1, 55))
document.add_picture(str(REPORT / 'ramaiah_logo.jpg'), width=Inches(2))
document.add_paragraph('Department of CSE (Artificial Intelligence & Machine Learning) and CSE (Cyber Security)')
for text, gap in [
    ('SELF LEARNING ACTIVITY REPORT', 14),
    ('Submitted in partial fulfilment of the Requirements for the Academics of 5th Semester, B.E in CSE (Artificial Intelligence and Machine Learning)', 13),
    ('DEVOPS', 5), ('25CIAEC59', 10), ('ConvertFlow - Unit Converter API', 10),
    ('In', 3), ('Dept. of CSE (Artificial Intelligence and Machine Learning)', 10),
    ('By', 3), ('Dhanekula Sathwika', 3), ('USN: 1MS24CI042', 15),
    ('Under the guidance of', 4), ('Mr. Prashanth Reddy C', 3), ('Senior Lecturer', 3),
    ('Department of CSE (AI & ML) and CSE (Cyber Security)', 15),
    ('M. S. Ramaiah Institute of Technology', 3),
    ('(Autonomous Institute Affiliated to VTU)\nMSR Nagar, MSRIT Post\nBangalore-560054, Karnataka, India', 0),
]:
    if text in ['SELF LEARNING ACTIVITY REPORT', 'DEVOPS']:
        title_style = ParagraphStyle('CenteredTitle', parent=styles['HReport'], alignment=1)
        story.extend([Paragraph(html.escape(text), title_style), Spacer(1, gap)])
    else:
        story.extend([paragraph(text, 'CenterReport'), Spacer(1, gap)])
    p = document.add_paragraph(text)
    p.alignment = 1
    p.paragraph_format.space_after = Pt(gap + 4)
    if text in ['SELF LEARNING ACTIVITY REPORT', 'DEVOPS']:
        p.runs[0].font.size = Pt(18); p.runs[0].bold = True
page(True)
story.extend([Spacer(1, 65), paragraph('Certificate', 'HReport'), Spacer(1, 25)])
document.add_heading('Certificate', 1)
certificate = ('This is to certify that the work carried out is a bonafide record of the project based learning activity work on the DevOps course done by Dhanekula Sathwika (1MS24CI042) under my supervision and guidance, in partial fulfilment of the requirements for the award of the Bachelor of Engineering in Computer Science & Engineering (Artificial Intelligence and Machine Learning) from Ramaiah Institute of Technology, Bangalore for the academic year 2026-2027.')
story.append(paragraph(certificate))
signature_labels = Table([['Candidate Sign', 'Faculty Sign']], colWidths=[290, 161])
signature_labels.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 12)]))
story.extend([Spacer(1, 150), signature_labels])
document.add_paragraph(certificate)
document.add_paragraph('\n\n\n\n\nCandidate Sign                                      Faculty Sign')
page(True)
story.append(paragraph('LIST OF PROJECT BASED LEARNING COMPONENTS', 'HReport'))
document.add_heading('LIST OF PROJECT BASED LEARNING COMPONENTS', 1)
course = 'COURSE NAME: DevOps     COURSE CODE: 25CIAEC59\nCREDITS: 1:0:0     CONTACT HOURS: 15L     MAX. MARKS: 20'
story.append(paragraph(course)); document.add_paragraph(course)
table([
    ['Sl. No', 'Description', 'Marks'],
    ['1', 'CI/CD Pipeline using Git, Maven/Gradle and Jenkins. Version control, feature branching and merging, dependency management, SCM-triggered Jenkins builds, post-build actions and a CI enhancement. Units 1-3; CO1, CO2, CO3.', '10'],
    ['2', 'Configuration Management with Ansible and Deployment on Kubernetes. Variables, handlers and a role; containerization, Deployment, Service, labels/selectors, scaling and a deployment enhancement. Units 4-5; CO4, CO5.', '10'],
], [44, 355, 52])
page(True)
story.append(paragraph('Assessment Rubrics', 'HReport')); document.add_heading('Assessment Rubrics', 1)
story.append(paragraph('Evaluation for each 10-mark component follows the supplied institutional rubric.'))
rows = [['Criteria', '2 - Good', '1 - Average', '0 - Poor']]
block = original[original.index('Concept Understanding (2 marks) &'):]
block = block[:block.index('\\end{longtable}')]
for row in block.split('\\hline'):
    if ' & ' in row:
        cells = row.strip().rstrip('\\').strip().split(' & ')
        cells = [re.sub(r'\\textbf\{([^}]+)\}', r'\1', c).replace('\\&', '&').replace('\\ ', ' ').replace('``', '"').replace("''", '"') for c in cells]
        if len(cells) == 4:
            rows.append(cells)
table(rows, [98, 120, 117, 116])
page(True)
story.append(paragraph('Marks Awarded', 'HReport')); document.add_heading('Marks Awarded', 1)
table([['Sl. No', 'Concept (2)', 'Core (2)', 'Enhancement (2)', 'Analysis (2)', 'Documentation (2)', 'Total'],
       ['1', '', '', '', '', '', ''], ['2', '', '', '', '', '', ''], ['TOTAL', '', '', '', '', '', '']],
      [35, 62, 60, 82, 62, 100, 50])
story.append(paragraph('Signatures and evaluator marks are intentionally blank.'))
page()
heading('Component 1: CI/CD Pipeline using Git, Maven and Jenkins')
heading('Abstract', 2)
body('ConvertFlow is a stateless REST API for unit conversion. GitHub hosts its preserved feature branch and merge history. Maven builds an executable JAR and runs 15 JUnit tests. A Jenkins Pipeline from SCM executes on a Linux executor, publishes test results, and archives the JAR. A new pushed commit was automatically built by SCM polling on this Ubuntu laptop.')
heading('Introduction', 2)
body('The aim is to turn each source revision into a tested artifact with traceable results. ConvertFlow keeps application behavior small enough to inspect while demonstrating version control, dependency management and continuous integration. Automated conversion and HTTP tests are the selected CI enhancement. Packaging is continuous integration; deployment to the systemd host and Kubernetes remains an explicit step.')
heading('Implementation', 2)
heading('Development Environment', 3)
body('Ubuntu 24.04.5 LTS on x86_64, OpenJDK 21.0.12.1, bundled Maven 3.9.9, JUnit Jupiter 5.11.4 and Jenkins 2.580.1 were used. Compilation targets Java 17. The Windows-only bundled JDK was not used. Jenkins listens on 127.0.0.1:8082 and has a Linux executor labelled linux. Pipeline, Git, JUnit and Timestamper plugins are installed and active. Maven 3.9.9 is provided on its PATH. Live versions and tool checksum verification are recorded in evidence/live/.')
heading('Code', 3)
body('The JDK HTTP server exposes GET /, /health and /convert. Conversion units are m/km/mi/ft, kg/g/lb and c/f/k. Invalid input returns HTTP 400; unknown paths return 404 and unsupported methods return 405. The app has no database or external runtime dependency. The following excerpt shows the conversion model; the complete Java sources and tests are included in the repository.')
code('src/main/java/in/ramaiah/convertflow/Converter.java', 1, 12)
body('pom.xml pins the test and build plugins, sets maven.compiler.release=17, and packages target/convertflow.jar with the App main class. The pipeline runs clean test before package; a failing test prevents the Package stage. JUnit XML is published in post, and successful runs archive the JAR with a fingerprint.')
code('Jenkinsfile')
heading('Description', 3)
body('Repository: ' + facts['repository'] + ' (private; authenticated account 1ms24ci042-DS). The existing main and feature/conversion-api branches and merge commit 4e3295b were preserved and pushed. Extraction differences were inspected: tracked changes were line-ending differences, with no content or mode changes before this continuation. A .gitattributes file now declares LF for scripts and source files. Existing history was not reset or rewritten.')
body('Jenkins job ConvertFlow uses Pipeline script from SCM, Git, branch */main and script path Jenkinsfile. Its GitHub credential is held in the encrypted Jenkins credential store, outside the project. The initial manual build #1 established the SCM baseline. The later documentation commit was pushed normally; no manual build request was used for build #2. The Jenkinsfile polls every two minutes using H/2 * * * *. This local setup uses polling so an inbound public webhook is unnecessary.')
heading('Enhancement with rationale', 2)
body('Automated tests give immediate feedback before packaging. Eight conversion tests cover normal unit conversions and boundary/error behavior; seven HTTP tests cover routing, query validation and response behavior. Both the local Maven build and Jenkins automatic build passed all 15 tests with zero failures, errors or skips. GitHub Actions supplies supplementary CI; recorded runs 39800624574 and 39801187031 also completed successfully. Jenkins evidence independently satisfies the required pipeline.')
heading('Results', 2)
body(f"Jenkins build #{facts['automatic_build']} completed SUCCESS in {facts['duration_seconds']:.3f} seconds, starting at {facts['build_timestamp']} UTC. Its cause is Started by an SCM change and its checked-out revision is {facts['automatic_commit']}. The JUnit API confirms 15 passed tests, zero failed and zero skipped; artifact metadata and a downloaded JAR verify archival. Evidence includes the pushed commit/time, build JSON, test JSON, polling log, console output and job XML.")
figure('terminal-git', 'GNOME Terminal: executed Git branch and merge history commands. The original feature branch and merge remain intact.')
figure('terminal-maven', 'GNOME Terminal: Maven clean verify was executed and its saved log tail shows BUILD SUCCESS and all 15 tests passing.')
figure('ubuntu-jenkins-scm', 'Jenkins configuration: Pipeline script from SCM with Git selected.')
figure('ubuntu-jenkins-repository', 'Genuine Jenkins UI: actual private repository URL and credential identifier, without exposing a credential value.')
figure('ubuntu-jenkins-script-path', 'Genuine Jenkins UI: branch */main and Jenkinsfile script path; lightweight checkout is enabled.')
figure('ubuntu-jenkins-polling', 'Jenkins SCM polling configuration, using the two-minute schedule from Jenkinsfile.')
figure('ubuntu-jenkins-auto-build', 'Actual Jenkins build #2 page showing the SCM change cause and archived convertflow.jar.')
figure('ubuntu-jenkins-auto-tests', 'Actual Jenkins JUnit report for the automatic build: all 15 tests passed.')
figure('ubuntu-jenkins-auto-console', 'Actual Jenkins console tail showing test-result publication, artifact archival and SUCCESS.')
body('The expected 5 km conversion is 3.1068559611866697 miles. Five packaged-service HTTP contract checks additionally verified health, length conversion, temperature conversion, incompatible dimensions and an unknown route. These results are recorded in host-api-checks.txt.')
heading('Conclusion', 2)
body('The verified workflow connects a real GitHub push to a tested and archived artifact through Jenkins SCM polling. The build cause and revision establish that the automatic run used the new commit. Separating tests from packaging makes the failure gate visible, while JUnit results and fingerprints make the output reviewable.')
refs([
    ('Apache Maven: Build Lifecycle', 'https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html'),
    ('Jenkins: Pipeline Syntax', 'https://www.jenkins.io/doc/book/pipeline/syntax/'),
    ('Git: merge documentation', 'https://git-scm.com/docs/git-merge'),
    ('Project repository', facts['repository']),
])
page()
heading('Component 2: Configuration Management with Ansible and Deployment on Kubernetes')
heading('Abstract', 2)
body('The same application is deployed to this Ubuntu system using an Ansible role and systemd, and to a local Kind cluster using a multi-stage Docker image. Ansible was run twice with zero changes on the second run. The container and Kubernetes Service returned correct responses. Three Ready replicas were scaled to five and then back to three, with readiness and exact counts checked at every step.')
heading('Introduction', 2)
body('Ansible expresses the host configuration as repeatable tasks, variables and change-triggered handlers. Docker packages the application runtime, and Kubernetes maintains the declared replica count and routes traffic through a Service. ConvertFlow is stateless, so replicas do not need shared storage. The deployment enhancement combines configuration injection and health checks, supported by a non-root multi-stage image.')
heading('Implementation', 2)
heading('Development Environment', 3)
body('The target is the actual Ubuntu 24.04 laptop with systemd, ansible-core 2.16.3 and Docker Engine 29.1.3. Kind v0.27.0 runs a Kubernetes v1.32.2 node, matched to kubectl v1.32.2. Cached Linux x86_64 binaries and the Jenkins WAR were checked against official SHA-256 values before use. The systemd app uses port 8080, Docker uses 8081, Jenkins uses 8082, and the Kubernetes Service is forwarded on 8083. The distinct ports allow all demonstrations to remain available.')
heading('Code', 3)
body('The inventory targets localhost through a local connection. Privileged tasks were reviewed before execution. They install a Java runtime, create the convertflow service user and /opt/convertflow, copy the built JAR, and write /etc/systemd/system/convertflow.service. File changes notify Restart ConvertFlow; pending handlers run before the health check. app_port, app_user, app_dir and app_jar are role variables.')
code('ansible/playbook.yml')
code('ansible/roles/convertflow/defaults/main.yml')
code('ansible/roles/convertflow/handlers/main.yml')
body('The systemd unit runs /usr/bin/java as the unprivileged convertflow user, restarts on failure, and enables NoNewPrivileges, ProtectSystem, ProtectHome and PrivateTmp. scripts/deploy-ubuntu.sh checks port ownership before replacing the known manually launched app with the service and runs the playbook twice.')
code('Dockerfile')
body('The build stage runs Maven clean verify. The runtime stage copies only the executable JAR into a Java 17 runtime image and runs as UID/GID 10001. Docker inspection and an actual id command confirm the non-root identity. The full Kubernetes manifest is k8s/deployment.yaml; the following excerpt declares the ConfigMap and replica selector.')
code('k8s/deployment.yaml', 1, 26)
heading('Description', 3)
body('The Docker image convertflow:1.0.0 was loaded into the named Kind cluster. The Deployment, its Pod template and the Service consistently select app=convertflow. The Service exposes 8080 with NodePort 30080; localhost:8083 is an active port-forward to that Service. EndpointSlice data confirms ready backend endpoints. scripts/deploy-kind.sh records 3 -> 5 -> 3; verify-replicas.py waits for the exact number of Ready Pods and no remaining terminating Pods, including after scale-down.')
heading('Enhancement with rationale', 2)
body('Readiness and liveness HTTP probes request /health. Readiness determines eligibility to receive Service traffic; liveness detects an unhealthy running process and can trigger restart. The ConfigMap supplies APP_PORT=8080, confirmed with printenv inside a live Pod. The multi-stage image excludes build tools from the runtime, and non-root settings reduce runtime privileges. These choices improve deployment consistency without introducing a database or extra service.')
body('Live evidence verifies configured probes, healthy Ready Pods, configuration injection and successful Service traffic. Deliberate process failure or a probe-induced restart was not part of this demonstration, so no fault-recovery event is claimed. Scaling is manual, not autoscaling. /health reports JSON application status and does not implement Prometheus metrics.')
heading('Results', 2)
body('Historical deployment on 22 October 2026 at approximately 20:26 IST: first run ok=9, changed=6, failed=0; original second run ok=8, changed=0, failed=0. The first-run transcript is preserved and displayed in a real terminal, clearly labelled as historical. During fresh verification, Maven rebuilt the JAR; a later Ansible run legitimately copied it and restarted the service (changed=2). The next unchanged run again reported ok=8, changed=0, failed=0. These fresh results and timestamps are recorded under evidence/terminal/. The active systemd service and health response are verified separately.')
body('Kubernetes recorded three Ready Pods, then five Ready Pods, then exactly three Ready Pods with none terminating. The same ReplicaSet remained responsible for the scaled workload. The Service returned UP and the expected 5 km conversion result. Live ConfigMap, Pod, Deployment, Service, EndpointSlice and node details are included in evidence/live/.')
figure('terminal-ansible-first-history', 'GNOME Terminal reviewing the preserved FIRST-RUN log from 22 October 2026, approximately 20:26 IST: restart handler and changed=6. This is historical log review, not a newly executed first deployment.')
figure('terminal-ansible-refresh', 'GNOME Terminal: after Maven rebuilt the JAR, Ansible legitimately copied the new artifact and ran its restart handler; changed=2. No role or service setting was altered to manufacture changes.')
figure('terminal-ansible-idempotent', 'GNOME Terminal: the subsequent unchanged Ansible run shows ok=8, changed=0, failed=0; no restart handler executes.')
figure('terminal-systemd', 'GNOME Terminal: actual active systemd service and successful health response on port 8080.')
figure('terminal-docker-build', 'GNOME Terminal: the Docker image build was executed; its real log tail confirms the completed image and convertflow:1.0.0 tag.')
figure('terminal-docker-runtime', 'GNOME Terminal: running Docker container, non-root runtime identity, health response and correct conversion result on port 8081.')
figure('terminal-kubernetes-3', 'GNOME Terminal: fresh verification of exactly three Ready Pods and the corresponding ReplicaSet before scaling.')
figure('terminal-kubernetes-5', 'GNOME Terminal: scale command to five replicas, exact readiness verification, and five Ready Pods.')
figure('terminal-kubernetes-down-3', 'GNOME Terminal: scale-down command and exact verification of three Ready Pods, with no terminating Pods remaining.')
figure('terminal-kubernetes-service', 'GNOME Terminal: actual Service configuration plus health and conversion responses through the Service port-forward on 8083.')
figure('terminal-kubernetes-config', 'GNOME Terminal: ConfigMap APP_PORT value and printenv inside a running Pod both show 8080, verifying configuration injection.')
figure('terminal-kubernetes-probes', 'GNOME Terminal: live readiness/liveness probe definitions, ConfigMap reference, and Deployment availability at three replicas.')
heading('Conclusion', 2)
body('The same application runs successfully as a systemd service, a Docker container and a Kubernetes workload. Ansible avoids unnecessary changes on the second run; Kubernetes reconciles the requested replica counts while the Service provides a stable access path. The demo remains running, and no cluster, image, container or service cleanup was performed.')
refs([
    ('Ansible: Handlers', 'https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_handlers.html'),
    ('Docker: Multi-stage builds', 'https://docs.docker.com/build/building/multi-stage/'),
    ('Kubernetes: Liveness and Readiness Probes', 'https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/'),
    ('Kind: Quick Start', 'https://kind.sigs.k8s.io/docs/user/quick-start/'),
    ('Project repository', facts['repository']),
])
page()
heading('Evidence and submission notes')
body('The preserved first deployment and Jenkins automatic build #2 occurred on 22 October 2026. Fresh terminal verification and scaling were also executed on this date; each terminal capture has a timestamped JSON record and an actual session transcript under evidence/terminal/. The historical first Ansible run is reviewed in a terminal and is explicitly distinguished from new execution. All command figures are direct gnome-screenshot captures of GNOME Terminal windows showing executed commands, output and prompts; Jenkins figures remain genuine browser UI captures. No terminal image, successful event or historical timestamp was synthesized. Superseded browser log views, failed focus captures and older rendered illustrations are excluded from the current reports and selected submission figures.')
body('The report uses portrait A4 pages for narrative and individual landscape A4 evidence pages to keep terminal text and Jenkins details readable. Body text and headings are black; screenshots retain their original colours. Page numbering continues across orientations.')
body('The supplied institutional original_template.tex defines the report structure and assessment rubric. A separate original assignment PDF was not found locally; the pre-existing ConvertFlow_Report.pdf was an earlier report. The two components each include Abstract, Introduction, Implementation, Enhancement with rationale, Results, Conclusion and References. Signatures and marks remain blank. No coordinator collaborator invitation is required, as instructed by the student.')
body('Repository: ' + facts['repository'] + '. The repository is private, so the evaluator needs authorized access or the clean submission ZIP. Credentials, dependency caches, bundled JDKs and unrelated files are excluded. The working repository and its full history are retained; the ZIP includes a Git bundle for history review and restore.')
body('Archived automatic-build JAR SHA-256: ' + facts['archived_jar_sha256'])
body('Live entry points: systemd http://localhost:8080/health; Docker http://localhost:8081/health; Jenkins http://localhost:8082/job/ConvertFlow/; Kubernetes http://localhost:8083/health. The port-forward and Jenkins WAR processes need restarting after reboot. The systemd service and Docker daemon are enabled. Full reproduction details are in README.md and the submitted scripts.')
tex.append('\\end{document}\n')
(REPORT / 'main.tex').write_text(''.join(tex))
(REPORT / 'figures-used.json').write_text(json.dumps(figures_used, indent=2) + '\n')


def footer(canvas, doc):
    if doc.page <= 2:
        canvas.drawImage(str(REPORT / 'ramaiah_logo.jpg'), 72, 777, width=147, height=45,
                         preserveAspectRatio=True, mask='auto')
        canvas.setFont('Times-Bold', 12)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(523, 804, 'Department of CSE (Artificial Intelligence &')
        canvas.drawRightString(523, 789, 'Machine Learning) and CSE (Cyber Security)')
        canvas.setStrokeColor(colors.HexColor('#8b1e3f'))
        canvas.setLineWidth(1.2); canvas.line(72, 768, 523, 768)
    else:
        canvas.setFont('Times-Roman', 12); canvas.setFillColor(colors.black)
        canvas.drawCentredString(canvas._pagesize[0] / 2, 38, str(doc.page - 2))


pdf = OUT / 'ConvertFlow_1MS24CI042_Report.pdf'
doc = BaseDocTemplate(str(pdf), pagesize=A4, rightMargin=72, leftMargin=72,
                     topMargin=55, bottomMargin=60, title='ConvertFlow - DevOps Report',
                     author='Dhanekula Sathwika')
doc.addPageTemplates([
    PageTemplate(id='Body', pagesize=A4, frames=[Frame(72, 60, A4[0]-144, A4[1]-115,
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer),
    PageTemplate(id='Evidence', pagesize=landscape(A4), frames=[Frame(72, 60,
                 landscape(A4)[0]-144, landscape(A4)[1]-115,
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer),
])
doc.build(story)
document.core_properties.title = 'ConvertFlow - DevOps Report'
document.core_properties.author = 'Dhanekula Sathwika'
document.save(OUT / 'ConvertFlow_1MS24CI042_Report.docx')
print('Generated PDF, DOCX and personalized LaTeX source; figures:', len(figures_used))
