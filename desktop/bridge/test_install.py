import json
from pathlib import Path
import tempfile
import unittest
from install import install

class InstallTests(unittest.TestCase):
    def test_preserves_other_settings_and_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);p=home/'.claude/settings.json';p.parent.mkdir()
            old={'permissions':{'defaultMode':'plan'},'autoMode':{'example':True},
                 'hooks':{'Stop':[{'hooks':[{'type':'command','command':'existing-handler'}]}]}}
            p.write_text(json.dumps(old));original=p.read_bytes()
            report,_=install(home,True)
            new=json.loads(p.read_text())
            self.assertEqual(new['permissions'],old['permissions'])
            self.assertEqual(new['hooks']['Stop'][0],old['hooks']['Stop'][0])
            self.assertEqual((Path(report['backups'])/'claude.json').read_bytes(),original)
            data=p.read_bytes();install(home,True);self.assertEqual(p.read_bytes(),data)
            self.assertFalse(report['codex_trust_changed'])

    def test_dry_run_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            install(tmp,False)
            self.assertEqual(list(Path(tmp).iterdir()),[])

if __name__=='__main__':unittest.main()
