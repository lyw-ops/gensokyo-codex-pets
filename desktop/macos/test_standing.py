"""Verify the bundle's standing timeline and explicit corrupt/missing asset behavior."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from import_standing import verify_package, SEQUENCE, POSE_FILES

binary = Path(sys.argv[1]).resolve()
source = binary.parent.parent / 'Resources/Standing'
checks = []
verify_package(source)
m = json.loads((source / 'source.json').read_text())
assert [f['file'] for f in m['frames']] == [POSE_FILES[i] for i in SEQUENCE]
checks.append('signed bundle contains byte-exact approved poses and all 140 frame selections')


def validate(root=source):
    return subprocess.run([str(binary), '--validate-assets', '--standing-root', str(root)],
                          capture_output=True, text=True)


r = validate()
assert r.returncode == 0, r.stderr
j = json.loads(r.stdout)
assert j['standing_frames'] == 140 and abs(j['standing_duration'] - 7) < 1e-9 and j['standing_reason'] == 'none', j
checks.append('native loader accepts the 7-second standing loop')
with tempfile.TemporaryDirectory(prefix='reimu-standing-qa-') as temp:
    root = Path(temp) / 'Standing'
    shutil.copytree(source, root)
    (root / 'poses/closed.png').write_bytes(b'corrupt')
    j = json.loads(validate(root).stdout)
    assert j['standing_frames'] == 1 and j['standing_reason'] != 'none' and j['frames'] == 40 and j['annoyed'] == 'verified', j
    checks.append('corrupt eye pose explicitly falls back to original standing without disabling reviewed interactions')
    (root / 'source.json').write_text('{}')
    j = json.loads(validate(root).stdout)
    assert j['standing_frames'] == 1 and j['standing_reason'] != 'none', j
    checks.append('corrupt manifest explicitly holds verified standing base')
    (root / 'base.png').unlink()
    r = validate(root)
    assert r.returncode == 1 and 'ASSET ERROR' in r.stderr, r
    checks.append('missing standing base fails closed instead of silently selecting a different drawing')
print(json.dumps({'status': 'pass', 'count': len(checks), 'checks': checks}, indent=2))
