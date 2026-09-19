"""Exercise the signed bundle's reaction loader, including damaged/missing artwork."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

binary = Path(sys.argv[1]).resolve()
def validate(*args):
    return json.loads(subprocess.check_output([str(binary), '--validate-assets', *args], text=True))
checks=[]
r=validate()
assert r['frames']==40 and abs(r['duration']-4)<1e-9 and r['annoyed']=='verified', r
checks.append('reviewed reaction and unchanged 40-frame clip load together')
with tempfile.TemporaryDirectory(prefix='reimu-reaction-qa-') as temp:
    root=Path(temp)
    r=validate('--reaction-root',str(root))
    assert r['annoyed']=='unavailable' and r['annoyed_reason']!='none' and r['status']=='animated',r
    checks.append('missing reaction degrades explicitly without disabling eating')
    (root/'annoyed.png').write_bytes(b'not the reviewed artwork')
    r=validate('--reaction-root',str(root))
    assert r['annoyed']=='unavailable' and r['annoyed_reason']!='none' and r['status']=='animated',r
    checks.append('corrupt reaction rejected without disabling eating')
print(json.dumps({'status':'pass','count':len(checks),'checks':checks},indent=2))
