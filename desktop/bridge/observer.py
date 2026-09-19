"""Passive local hook observer. Never returns permission or continuation decisions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

EVENTS = {
    'SessionStart', 'SessionEnd', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse',
    'PermissionRequest', 'Stop', 'Interrupt', 'SubagentStart', 'SubagentStop',
    'Notification', 'StopFailure', 'PostToolUseFailure', 'Elicitation', 'ElicitationResult',
}
DEFAULT_ROOT = Path.home() / 'Library/Application Support/ReimuCompanion'
STALE_SECONDS = 600


def identifier(value):
    if not isinstance(value, str) or not value or len(value) > 4096:
        return None
    return hashlib.sha256(value.encode()).hexdigest()[:32]


def normalize(provider, raw, now=None):
    if provider not in ('codex', 'claude') or not isinstance(raw, dict):
        return None
    name = raw.get('hook_event_name')
    session = identifier(raw.get('session_id'))
    if name not in EVENTS or not session:
        return None
    # An explicit child indicator prevents a child's tools from becoming a main task.
    child = identifier(raw.get('agent_id'))
    if name in ('SubagentStart', 'SubagentStop') and not child:
        return None
    if child and name not in ('SubagentStart', 'SubagentStop'):
        return None
    notice = raw.get('notification_type')
    # idle_prompt is not a reliable "task completed" event.
    if name == 'Notification' and notice not in ('permission_prompt', 'elicitation_dialog', 'elicitation_url_dialog'):
        return None
    return {'provider': provider, 'session': session, 'turn': identifier(raw.get('turn_id')),
            'event': name, 'child': child, 'received_at': time.time() if now is None else now}


def reduce_record(previous, event):
    """Idempotent state updates: session keys, rather than event increments, count tasks."""
    old = dict(previous) if previous else {}
    name, stamp = event['event'], event['received_at']
    if old and stamp < old['updated_at']:
        return old
    old_turn, new_turn = old.get('turn'), event['turn']
    if old_turn and new_turn and old_turn != new_turn and name != 'UserPromptSubmit':
        return old  # A delayed end/tool event cannot stop a newer turn.
    result = old or {'provider': event['provider'], 'session': event['session'],
                     'turn': new_turn, 'state': 'idle', 'updated_at': stamp}
    state = result['state']
    if name == 'UserPromptSubmit':
        result['turn'] = new_turn
        state = 'working'
    elif name == 'SessionStart':
        # Startup is not work; compact/resume must not reset an ongoing turn.
        pass
    elif name in ('PreToolUse', 'PostToolUse', 'PostToolUseFailure'):
        if state not in ('round_ended', 'interrupted', 'failed', 'closed'):
            state = 'working'  # A failed tool can be recovered by the agent.
    elif name in ('PermissionRequest', 'Notification', 'Elicitation'):
        if state not in ('round_ended', 'interrupted', 'failed', 'closed'):
            state = 'needs_input'
    elif name == 'ElicitationResult':
        if state == 'needs_input':
            state = 'working'
    elif name == 'Stop':
        state = 'round_ended'  # Not success, certification or complete project work.
    elif name == 'Interrupt':
        state = 'interrupted'
    elif name == 'StopFailure':
        state = 'failed'
    elif name == 'SessionEnd':
        # Don't erase a just-reported turn ending when a one-shot client exits.
        state = state if state in ('round_ended', 'interrupted', 'failed') else 'closed'
    result.update(state=state, updated_at=stamp)
    return result


def summarize(records, now=None):
    now = time.time() if now is None else now
    states = []
    for record in records:
        state = record['state']
        age = max(0, now - record['updated_at'])
        if state in ('working', 'needs_input') and age > STALE_SECONDS:
            state = 'unknown'
        if state in ('round_ended', 'interrupted', 'failed') and age > 30:
            state = 'idle'
        states.append(state)
    running = states.count('working')
    priority = ['needs_input', 'failed', 'working', 'unknown', 'round_ended', 'interrupted']
    state = next((s for s in priority if s in states), 'idle' if states else 'disconnected')
    return {'state': state, 'observed_active_tasks': running,
            'unknown_sessions': states.count('unknown'),
            'coverage': 'hook-observed sessions only; not a census of all application tasks'}


def persist(root, event):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    db_path = root / 'events.sqlite3'
    conn = sqlite3.connect(str(db_path), timeout=0.25, isolation_level=None)
    os.chmod(db_path, 0o600)
    try:
        conn.execute('PRAGMA busy_timeout=250')
        conn.execute('CREATE TABLE IF NOT EXISTS sessions (key TEXT PRIMARY KEY, record TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS children (key TEXT PRIMARY KEY, parent TEXT, active INTEGER, updated_at REAL)')
        conn.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, provider TEXT, event TEXT, session TEXT, turn TEXT, received_at REAL)')
        conn.execute('BEGIN IMMEDIATE')
        key = event['provider'] + ':' + event['session']
        row = conn.execute('SELECT record FROM sessions WHERE key=?', (key,)).fetchone()
        previous = json.loads(row[0]) if row else None
        if event['event'] in ('SubagentStart', 'SubagentStop'):
            child_key = event['provider'] + ':' + event['child']
            conn.execute('INSERT INTO children VALUES (?,?,?,?) ON CONFLICT(key) DO UPDATE SET active=excluded.active,updated_at=excluded.updated_at WHERE excluded.updated_at>=children.updated_at',
                         (child_key, key, int(event['event'] == 'SubagentStart'), event['received_at']))
        else:
            record = reduce_record(previous, event)
            conn.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)', (key, json.dumps(record)))
            if event['event'] in ('Stop','Interrupt','StopFailure','SessionEnd') and record['updated_at'] == event['received_at']:
                conn.execute('UPDATE children SET active=0 WHERE parent=?', (key,))
        conn.execute('INSERT INTO events(provider,event,session,turn,received_at) VALUES (?,?,?,?,?)',
                     tuple(event[k] for k in ('provider','event','session','turn','received_at')))
        # Bounded metadata retention; no prompt, transcript, tool arguments or output is saved.
        conn.execute('DELETE FROM events WHERE id <= (SELECT COALESCE(MAX(id),0)-2048 FROM events)')
        conn.execute('DELETE FROM children WHERE updated_at < ?', (time.time()-86400,))
        conn.execute('DELETE FROM sessions WHERE key NOT IN (SELECT key FROM sessions ORDER BY json_extract(record,\'$.updated_at\') DESC LIMIT 256)')
        records = [json.loads(row[0]) for row in conn.execute('SELECT record FROM sessions ORDER BY key')]
        children = conn.execute('SELECT count(*) FROM children WHERE active=1 AND updated_at>?', (time.time()-STALE_SECONDS,)).fetchone()[0]
        snapshot = {'schema_version':1, 'written_at':time.time(), 'stale_seconds':STALE_SECONDS,
                    'sessions':records, 'observed_active_children':children, 'summary':summarize(records)}
        target = root / 'snapshot.json'
        temp = root / ('snapshot.%d.tmp' % os.getpid())
        fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd,'w') as f:
            json.dump(snapshot,f,ensure_ascii=False,allow_nan=False)
            f.flush()
        # Kept inside the write lock so a concurrent old snapshot cannot overwrite a newer one.
        os.replace(str(temp), str(target))
        conn.execute('COMMIT')
        return snapshot
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', choices=['codex','claude'], required=True)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(8*1024*1024+1)
        if len(raw) <= 8*1024*1024:
            event = normalize(args.provider, json.loads(raw))
            if event:
                persist(args.root,event)
    except Exception:
        pass  # Observer failure must never block, approve or continue the agent.
    print('{}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
