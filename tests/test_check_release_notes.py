import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_release_notes.py'

class ReleaseCheckerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = {'version':'1.22.0','date':'2026-10-29','notes':['Old note.']}
        self.new = {'version':'1.23.0','date':'2026-11-10','notes':['Choose "Save" in C:\\Reports; $(date) `echo hi` 😀', '<a href="https://example.com/?a=1&amp;b=2">Read</a>'], 'announcement':'We’re ready!', 'pinned': [{'flag':'release-welcome','message':'Read <b>this</b>'}]}
        subprocess.run(['git','init','-q'],cwd=self.root,check=True)
        for name in ('flex-enterprise.json','flex-assets.json'):
            (self.root/name).write_text(json.dumps([self.old]))
        subprocess.run(['git','add','.'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','baseline'],cwd=self.root,check=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_check(self, raw=None):
        (self.root/'flex-enterprise.json').write_text(raw if raw is not None else json.dumps([self.new,self.old]))
        return subprocess.run([sys.executable,str(SCRIPT),'--base','HEAD'],cwd=self.root,capture_output=True,text=True)

    def test_exact_decoded_text_and_no_mutation(self):
        result=self.run_check()
        self.assertEqual(result.returncode,0,result.stderr)
        for note in self.new['notes']:
            self.assertIn(note,result.stdout)
        self.assertIn('release-welcome',result.stdout)
        self.assertIn('We’re ready!',result.stdout)
        self.assertEqual(json.loads((self.root/'flex-enterprise.json').read_text()),[self.new,self.old])

    def test_invalid_inputs(self):
        for raw in ('[{', json.dumps([dict(self.new,date='2026-02-30')]), json.dumps([dict(self.new,pinned={'message':'Hi'})]), json.dumps([dict(self.new,notes='not an array')]), json.dumps([dict(self.new,version='not-semver')]), json.dumps([dict(self.new,version='highlight-test',highlight=True)]), json.dumps([self.new,self.new,self.old]), '[{"version":"1.23.0","version":"1.23.1","date":"2026-11-10","notes":[]}]', '[{"version":"1.23.0","date":"2026-11-10","notes":[],"unknown":NaN}]'):
            with self.subTest(raw=raw):
                self.assertNotEqual(self.run_check(raw).returncode,0)

    def test_existing_version_edit_and_object_pin(self):
        self.new['version']='1.22.0'
        self.new['pinned']=self.new['pinned'][0]
        self.assertEqual(self.run_check(json.dumps([self.new])).returncode,0)

    def test_jq_gate_blocks_empty_array_and_missing_jq(self):
        result = self.run_check('[]')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CI jq validation failed for flex-enterprise.json', result.stderr)
        tools = self.root / 'bin'
        tools.mkdir()
        (tools / 'git').symlink_to(shutil.which('git'))
        result = subprocess.run([sys.executable, str(SCRIPT), '--base', 'HEAD'],
                                cwd=self.root, capture_output=True, text=True,
                                env={**os.environ, 'PATH': str(tools)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CI jq validation failed', result.stderr)
        self.assertIn('jq', result.stderr)

    def test_schema_checks_unchanged_entries_and_preserves_legacy_labels(self):
        for notes, expected in [(['Historical copy.'], 0), ('invalid notes', 1)]:
            legacy = dict(self.old, version='Historical announcement', notes=notes)
            for name in ('flex-enterprise.json', 'flex-assets.json'):
                (self.root/name).write_text(json.dumps([legacy]))
            subprocess.run(['git','add','.'],cwd=self.root,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid',
                            'commit','-qm','legacy baseline'],cwd=self.root,check=True)
            result = self.run_check(json.dumps([legacy]))
            self.assertEqual(result.returncode, expected, result.stderr)

    def test_highlight(self):
        self.new.update(version='highlight-training-2026',highlight=True,title='Training')
        self.assertEqual(self.run_check().returncode,0)

    def test_baseline_duplicate_is_warning_but_changed_duplicate_fails(self):
        raw='[{"version":"1.22.0","date":"2026-10-29","notes":[],"pinned":{"flag":"known","flag":"known","message":"Hello"}}]'
        for name in ('flex-enterprise.json','flex-assets.json'):
            (self.root/name).write_text(raw)
        subprocess.run(['git','add','.'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','existing duplicate'],cwd=self.root,check=True)
        result=self.run_check(raw)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Baseline duplicate-key warnings',result.stdout)
        self.assertNotEqual(self.run_check(raw.replace('Hello','Changed')).returncode,0)
        self.assertNotEqual(self.run_check(raw.replace('\"flag\":\"known\",', '\"flag\":\"known\",\"flag\":\"known\",', 1)).returncode,0)

if __name__=='__main__':
    unittest.main()
