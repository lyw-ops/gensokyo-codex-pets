"""Install passive observers without changing existing policies or trusting Codex hooks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import time

CODEX_EVENTS = ['SessionStart','UserPromptSubmit','PermissionRequest','PreToolUse','PostToolUse',
                'Stop','Interrupt','SessionEnd','SubagentStart','SubagentStop']
CLAUDE_EVENTS = ['SessionStart','UserPromptSubmit','PermissionRequest','PreToolUse','PostToolUse',
                 'PostToolUseFailure','Stop','StopFailure','SessionEnd','SubagentStart','SubagentStop',
                 'Notification','Elicitation','ElicitationResult']


def definitions(provider, script, state_root):
    command = ' '.join(map(shlex.quote, ['/usr/bin/python3',str(script),'--provider',provider,'--root',str(state_root)]))
    events = CODEX_EVENTS if provider == 'codex' else CLAUDE_EVENTS
    result = {}
    for event in events:
        group = {'hooks':[{'type':'command','command':command,'timeout':1}]}
        if event == 'Notification':
            group['matcher'] = 'permission_prompt|elicitation_dialog|elicitation_url_dialog'
        result[event] = [group]
    return result


def merge(original, additions):
    result = json.loads(json.dumps(original))
    hooks = result.setdefault('hooks',{})
    for event,groups in additions.items():
        existing=hooks.setdefault(event,[])
        for group in groups:
            if group not in existing:existing.append(group)
    return result


def install(home, apply=False):
    home=Path(home)
    root=home/'Library/Application Support/ReimuCompanion'
    script=root/'observer.py'
    paths={'codex':home/'.codex/hooks.json','claude':home/'.claude/settings.json'}
    originals={}
    outputs={}
    for provider,path in paths.items():
        assert not path.is_symlink(), 'Refuse to replace a symlinked settings file'
        originals[provider]=path.read_bytes() if path.exists() else None
        original=json.loads(originals[provider]) if originals[provider] else {}
        outputs[provider]=merge(original,definitions(provider,script,root))
    report={'state_root':str(root),'observer':str(script),'applied':apply,
            'codex_requires_user_hook_trust':True,'codex_trust_changed':False,
            'configs':{provider:str(path) for provider,path in paths.items()}}
    if apply:
        root.mkdir(parents=True,exist_ok=True,mode=0o700)
        backups=root/('backups/'+str(time.time_ns()));backups.mkdir(parents=True,mode=0o700)
        if script.exists():shutil.copyfile(script,backups/'observer.py')
        source=Path(__file__).with_name('observer.py').read_bytes()
        script_temp=script.with_name('observer.reimu-install.tmp');assert not script_temp.exists()
        fd=os.open(str(script_temp),os.O_WRONLY | os.O_CREAT | os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(source)
        os.replace(script_temp,script)
        for provider,path in paths.items():
            # Check for edits since the read before touching user settings.
            current=path.read_bytes() if path.exists() else None
            assert current==originals[provider], 'Settings changed during install'
            if current is not None:
                backup=backups/(provider+'.json');backup.write_bytes(current);os.chmod(backup,0o600)
            path.parent.mkdir(parents=True,exist_ok=True)
            temp=path.with_name(path.name+'.reimu-install.tmp');assert not temp.exists()
            temp.write_text(json.dumps(outputs[provider],ensure_ascii=False,indent=2)+'\n');os.chmod(temp,0o600)
            os.replace(temp,path)
            after=json.loads(path.read_text())
            before=json.loads(current) if current else {}
            assert {k:v for k,v in after.items() if k!='hooks'} == {k:v for k,v in before.items() if k!='hooks'}
        report['backups']=str(backups)
        report['observer_sha256']=hashlib.sha256(source).hexdigest()
        (root/'installation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report,outputs


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--home',type=Path,default=Path.home())
    a=p.parse_args();report,outputs=install(a.home,a.apply);print(json.dumps(report,ensure_ascii=False,indent=2))
