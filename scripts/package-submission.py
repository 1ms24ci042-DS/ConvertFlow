#!/usr/bin/env python3
"""Package committed source, curated evidence, reports and preserved Git history."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'submission'
out.mkdir(exist_ok=True)
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
tracked = [p for p in tracked if p]
bundle = out / 'ConvertFlow-history.bundle'
subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], cwd=root, check=True)
subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=root, check=True)
entries = [(root / p, 'ConvertFlow/project/' + p) for p in tracked]
for name in ['ConvertFlow_1MS24CI042_Report.pdf', 'ConvertFlow_1MS24CI042_Report.docx']:
    entries.append((out / name, 'ConvertFlow/reports/' + name))
entries.append((bundle, 'ConvertFlow/ConvertFlow-history.bundle'))
entries.append((out / 'convertflow-build-2.jar', 'ConvertFlow/artifacts/convertflow-build-2.jar'))
entries.extend((p, 'ConvertFlow/evidence/junit/' + p.name)
               for p in (root / 'target/surefire-reports').glob('TEST-*.xml'))
entries.append((out / 'README.txt', 'ConvertFlow/README.txt'))
manifest = []
archive = out / 'ConvertFlow_1MS24CI042_Submission.zip'
for path, name in entries:
    assert path.is_file(), path
    assert not any(x in name.split('/') for x in ['.git', '.aws', '.codex', '.agents', '__pycache__'])
    data = path.read_bytes()
    manifest.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for path, name in entries:
        z.write(path, name)
    z.writestr('ConvertFlow/MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist()) == len(set(z.namelist()))
(out / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
checksums = []
for p in [archive, bundle, out / 'ConvertFlow_1MS24CI042_Report.pdf',
          out / 'ConvertFlow_1MS24CI042_Report.docx', out / 'convertflow-build-2.jar']:
    checksums.append(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name)
(out / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n')
print('Created', archive, 'with', len(manifest), 'files plus manifest;', archive.stat().st_size, 'bytes')
