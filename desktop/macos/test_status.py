"""Cross-language contract smoke test against an explicitly built native executable."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bridge'))
from observer import normalize, reduce_record, summarize


def main(binary):
    cases = [[], ['SessionStart'], ['UserPromptSubmit'], ['PermissionRequest'],
             ['Stop'], ['Interrupt'], ['StopFailure'], ['UserPromptSubmit', 'PermissionRequest']]
    count = 0
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'snapshot.json'
        def read(now):
            return json.loads(subprocess.check_output(
                [binary, '--status-snapshot', str(path), '--at', str(now)], text=True))
        for events in cases:
            records = [reduce_record(None, normalize('codex', {
                'session_id': str(i), 'hook_event_name': name}, 1000))
                for i, name in enumerate(events)]
            path.write_text(json.dumps({'schema_version': 1, 'stale_seconds': 600, 'sessions': records}))
            for now in [1001, 1031, 1701]:
                expected, actual = summarize(records, now), read(now)
                assert actual['state'] == expected['state'], (events, now, actual)
                assert actual['active'] == expected['observed_active_tasks']
                assert actual['unknown'] == expected['unknown_sessions']
                count += 1
        for malformed in ['not json', '{"schema_version":2}',
                          json.dumps({'schema_version':1,'stale_seconds':1,'sessions':[]})]:
            path.write_text(malformed)
            assert read(1001)['state'] == 'unknown'
            count += 1
        path.unlink()
        assert read(1001)['state'] == 'disconnected'
        count += 1
    print(json.dumps({'status': 'pass', 'cases': count, 'source': 'synthetic contract fixtures'}))


if __name__ == '__main__':
    main(str(Path(sys.argv[1]).resolve()))
