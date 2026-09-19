"""Package the approved Harness standing loop without resizing or rerendering it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE_SHA = '4b390982469cedbc3b1a0b3792c49a686e2b87b7dda6e5ab12d7bc73cd3e75e7'
POSE_SHA = [BASE_SHA, '5ef2010afaab9510907d0db4b7c93f367bf87806b5dd66af6a76ccaf80158da2',
            '1fd7096fe4821c08b2c478238fa884d88e9a9ea1209613c74ebe3a84e066f6f8']
POSE_FILES = ['base.png', 'poses/half.png', 'poses/closed.png']
PLAN_DIGEST = 'sha256:a02cec3e87f0aba18c31dd5c97e66f97755fdb12e8f465d0bf4438f5a8c393c1'
SEQUENCE = [0] * 96 + [1, 2, 2, 1, 1] + [0] * 39


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    return {'exact_frame_source_version': 1, 'character': 'reimu',
            'state_set': 'neutral_standing_v1', 'state': 'idle_blink',
            'canvas': {'width': 1254, 'height': 1254},
            'playback': {'fps': 20, 'frame_count': 140, 'loop': True},
            'base': {'file': 'base.png', 'sha256': BASE_SHA},
            'frames': [{'file': POSE_FILES[i], 'duration_ms': 50, 'sha256': POSE_SHA[i]} for i in SEQUENCE],
            'provenance': {'harness_plan_digest': PLAN_DIGEST, 'source_base_sha256': BASE_SHA,
                           'transformation': 'byte-exact deduplication only',
                           'visual_approval': 'user confirmed standing blink v1 on 2026-09-07'}}


def verify_package(root):
    if json.loads((root / 'source.json').read_text()) != manifest():
        raise ValueError('Standing manifest differs from the approved sequence')
    for name, digest in zip(POSE_FILES, POSE_SHA):
        if sha(root / name) != digest:
            raise ValueError(f'Standing pose identity mismatch: {name}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--harness-root', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True, help='Approved final/ build')
    p.add_argument('--reduced-source', type=Path, required=True, help='Approved reduced-final/ build')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise ValueError('Refuse to overwrite a package')
    env = dict(os.environ, PYTHONPATH='src')
    reports, payloads = {}, {}
    for mode, root in [('full', a.source.resolve()), ('hold_first_frame', a.reduced_source.resolve())]:
        result = subprocess.run([sys.executable, '-m', 'sprite_harness', 'validate', str(root), '--json'],
                                cwd=a.harness_root.resolve(), env=env, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        if not report['valid'] or report['errors'] or report['warnings'] or report['mode'] != mode:
            raise ValueError(f'Harness validation failed: {report}')
        frame_plan = json.loads((root / 'frame-plan.json').read_text())
        if frame_plan['plan_digest'] != PLAN_DIGEST or len(frame_plan['frames']) != 140:
            raise ValueError('Not the approved Harness plan')
        for i, pose in enumerate(SEQUENCE):
            record = frame_plan['frames'][i]
            if record['file'] != f'frames/frame_{i:03d}.png':
                raise ValueError('Unexpected Harness frame path')
            data = (root / record['file']).read_bytes()
            expected = POSE_SHA[pose] if mode == 'full' else BASE_SHA
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f'Unapproved source frame {mode}/{i}')
            if mode == 'full':
                payloads[POSE_FILES[pose]] = data
        reports[mode] = report
    # All source bytes have been verified and frozen in memory before writing the new output.
    a.out.mkdir(parents=True, exist_ok=False)
    for name, data in payloads.items():
        path = a.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (a.out / 'source.json').write_text(json.dumps(manifest(), ensure_ascii=False, indent=2) + '\n')
    verify_package(a.out)
    print(json.dumps({'output': str(a.out.resolve()), 'manifest_sha256': sha(a.out / 'source.json'),
                      'unique_images': 3, 'frame_count': 140, 'duration_ms': 7000,
                      'harness_validation': reports}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
