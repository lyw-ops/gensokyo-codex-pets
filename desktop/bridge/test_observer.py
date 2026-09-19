import concurrent.futures
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from observer import normalize, persist, reduce_record, summarize


def event(name, session='session-1', turn='turn-1', at=100, provider='codex', **extra):
    return normalize(provider,dict(hook_event_name=name,session_id=session,turn_id=turn,**extra),at)


class ObserverTests(unittest.TestCase):
    def test_work_wait_resume_end(self):
        record = None
        for n,s in [('SessionStart','idle'),('UserPromptSubmit','working'),('PermissionRequest','needs_input'),
                    ('PostToolUse','working'),('Stop','round_ended'),('SessionEnd','round_ended')]:
            record=reduce_record(record,event(n))
            self.assertEqual(record['state'],s)

    def test_old_turn_cannot_stop_new_turn(self):
        r=reduce_record(None,event('UserPromptSubmit'))
        r=reduce_record(r,event('UserPromptSubmit',turn='next',at=101))
        self.assertEqual(reduce_record(r,event('Stop',at=102)),r)
        self.assertEqual(reduce_record(r,event('PermissionRequest',turn='next',at=90)),r)

    def test_late_tool_cannot_resurrect_ended_turn(self):
        r=reduce_record(None,event('Stop'))
        self.assertEqual(reduce_record(r,event('PostToolUse',at=101))['state'],'round_ended')
        self.assertEqual(reduce_record(r,event('UserPromptSubmit',at=102))['state'],'working')

    def test_tool_failure_is_not_task_failure(self):
        r=reduce_record(None,event('PostToolUseFailure',provider='claude'))
        self.assertEqual(r['state'],'working')
        self.assertEqual(reduce_record(r,event('StopFailure',at=101,provider='claude'))['state'],'failed')

    def test_interrupted_is_not_completed(self):
        self.assertEqual(reduce_record(None,event('Interrupt'))['state'],'interrupted')

    def test_unknown_instead_of_invented_zero(self):
        r=reduce_record(None,event('UserPromptSubmit'))
        s=summarize([r],701)
        self.assertEqual((s['state'],s['unknown_sessions']),('unknown',1))
        self.assertEqual(summarize([],701)['state'],'disconnected')

    def test_uncapped_count_and_priority(self):
        records=[reduce_record(None,event('UserPromptSubmit',session=str(i))) for i in range(8)]
        s=summarize(records,101)
        self.assertEqual(s['observed_active_tasks'],8)
        self.assertNotIn('food_tier',s)  # The existing app policy owns visual tiers.
        records.append(reduce_record(None,event('PermissionRequest',session='wait')))
        self.assertEqual(summarize(records,101)['state'],'needs_input')

    def test_no_content_or_raw_identifiers_saved(self):
        raw={'hook_event_name':'UserPromptSubmit','session_id':'private-session','turn_id':'private-turn',
             'prompt':'SECRET PROMPT','cwd':'SECRET DIRECTORY','last_assistant_message':'SECRET ANSWER'}
        e=normalize('codex',raw)
        with tempfile.TemporaryDirectory() as tmp:
            persist(tmp,e)
            for path in Path(tmp).iterdir():
                data=path.read_bytes()
                self.assertNotIn(b'SECRET',data)
                self.assertNotIn(b'private-session',data)

    def test_children_dont_inflate_main_task_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            persist(tmp,event('UserPromptSubmit'))
            snapshot=persist(tmp,event('SubagentStart',agent_id='child',at=101))
            self.assertEqual(len(snapshot['sessions']),1)
            self.assertIsNone(normalize('claude',{'hook_event_name':'PreToolUse','session_id':'child','agent_id':'child'}))

    def test_concurrent_hooks_no_lost_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            persist(tmp,event('SessionStart'))
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(lambda i:persist(tmp,event('UserPromptSubmit',session=str(i))),range(24)))
            result=json.loads((Path(tmp)/'snapshot.json').read_text())
            self.assertEqual(len(result['sessions']),25)
            self.assertEqual(summarize(result['sessions'],101)['observed_active_tasks'],24)

    def test_duplicate_submit_does_not_increment_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            for _ in range(3):snapshot=persist(tmp,event('UserPromptSubmit'))
            self.assertEqual(len(snapshot['sessions']),1)

    def test_passive_cli_on_invalid_or_unwritable_input(self):
        script=Path(__file__).with_name('observer.py')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'file';root.write_text('not a directory')
            for payload in ['not json',json.dumps({'session_id':'s','hook_event_name':'UserPromptSubmit'})]:
                p=subprocess.run([sys.executable,str(script),'--provider','codex','--root',str(root)],
                                 input=payload,text=True,capture_output=True,timeout=2)
                self.assertEqual((p.returncode,p.stdout,p.stderr),(0,'{}\n',''))


if __name__=='__main__':unittest.main()
