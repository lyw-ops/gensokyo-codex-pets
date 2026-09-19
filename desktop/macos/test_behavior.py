"""Compile and exercise the input/state machine without UI or live provider writes."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='reimu-behavior-tests-') as tmp:
    tmp = Path(tmp)
    (tmp / 'main.swift').write_bytes((root / 'test_behavior.swift').read_bytes())
    subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', str(root / 'PetBehavior.swift'),
                    str(tmp / 'main.swift'), '-o', str(tmp / 'tests')], check=True)
    subprocess.run([str(tmp / 'tests')], check=True)
