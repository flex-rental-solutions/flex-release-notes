import json
import os
import shutil
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.check_release_notes import VALIDATOR, schema_errors, validate_entry

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

    def run_check(self, raw=None, allow_edited_notes=False):
        (self.root/'flex-enterprise.json').write_text(raw if raw is not None else json.dumps([self.new,self.old]))
        args = [sys.executable, str(SCRIPT), '--base', 'HEAD']
        if allow_edited_notes:
            args.append('--allow-edited-notes')
        return subprocess.run(args,cwd=self.root,capture_output=True,text=True)

    def test_supported_bullet_formats(self):
        edited = {'text': self.new['notes'][0], 'editedDate': '2026-10-22'}
        for notes in (self.new['notes'], [edited], [self.new['notes'][1], edited], [], ['']):
            with self.subTest(notes=notes):
                entry = dict(self.new, notes=notes)
                self.assertEqual(schema_errors(VALIDATOR, [entry]), [])
                self.assertEqual(validate_entry(entry), [])
                result = self.run_check(json.dumps([entry, self.old]), allow_edited_notes=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                for note in notes:
                    text = note['text'] if isinstance(note, dict) else note
                    self.assertIn(text, result.stdout)
                if edited in notes:
                    self.assertIn('editedDate: 2026-10-22', result.stdout)
                self.assertEqual(json.loads((self.root/'flex-enterprise.json').read_text()),
                                 [entry, self.old])

    def test_invalid_bullet_objects(self):
        edited = {'text': 'Edited bullet.', 'editedDate': '2026-10-22'}
        invalid = [{}, {'text': 'Missing date.'}, {'editedDate': '2026-10-22'},
                   dict(edited, extra='unexpected'), None, 1, True, ['nested']]
        invalid += [dict(edited, text=value) for value in ('', ' \n\t', None, 1, True, [], {})]
        invalid += [dict(edited, editedDate=value) for value in (
            '', None, 20261022, True, [], {}, '2026-2-03', '26-10-22', '10/22/2026',
            '2026-10-22T00:00:00Z', '2026-10-22 ', '2026-10-22\n',
            '2026-02-30', '2026-13-01', '2026-00-01', '2026-10-00', '2025-02-29')]
        for note in invalid:
            with self.subTest(note=note):
                entry = dict(self.new, notes=['Legacy bullet.', note])
                self.assertTrue(schema_errors(VALIDATOR, [entry]))
                self.assertTrue(validate_entry(entry))
        leap_day = dict(self.new, notes=[dict(edited, editedDate='2024-02-29')])
        self.assertEqual(validate_entry(leap_day), [])
        result = self.run_check(json.dumps([dict(self.new, notes=[dict(edited, editedDate='2026-02-30')])]),
                                allow_edited_notes=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('notes[0]', result.stderr)

    def test_object_publication_gate_covers_both_plans_and_unchanged_entries(self):
        entry = dict(self.old, notes=[{'text': 'Edited bullet.', 'editedDate': '2026-10-22'}])
        for filename in ('flex-enterprise.json', 'flex-assets.json'):
            with self.subTest(filename=filename):
                for name in ('flex-enterprise.json', 'flex-assets.json'):
                    (self.root/name).write_text(json.dumps([entry if name == filename else self.old]))
                subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
                subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                                'commit', '-qm', 'object baseline'], cwd=self.root, check=True)
                raw = (self.root/'flex-enterprise.json').read_text()
                result = self.run_check(raw)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'{filename} 1.22.0: object bullets are blocked for publication', result.stderr)
                self.assertIn('PR #4905', result.stderr)
                allowed = self.run_check(raw, allow_edited_notes=True)
                self.assertEqual(allowed.returncode, 0, allowed.stderr)
                self.assertIn('No content changes.', allowed.stdout)

    def test_new_object_publication_and_duplicate_keys(self):
        raw = '[{"version":"1.23.0","date":"2026-11-10","notes":[{"text":"Edited bullet.","editedDate":"2026-10-22"}]}]'
        result = self.run_check(raw)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('object bullets are blocked for publication', result.stderr)
        for key, value in (('text', 'Shadowed text.'), ('editedDate', '2026-10-21')):
            with self.subTest(key=key):
                duplicate = raw.replace(f'"{key}":', f'"{key}":"{value}","{key}":')
                result = self.run_check(duplicate, allow_edited_notes=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'duplicate key $.notes[0].{key}', result.stderr)

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

    def test_new_major_zero_patch_versions_fail(self):
        for version in ('0.28.1', '0.0.1', '00.28.001'):
            with self.subTest(version=version):
                result=self.run_check(json.dumps([dict(self.new,version=version),self.old]))
                self.assertNotEqual(result.returncode,0,result.stdout)
                self.assertIn('version',result.stderr)

    def test_current_version_conventions_preserve_historical_major_zero_entries(self):
        legacy=dict(self.old,version='0.27.39')
        for name in ('flex-enterprise.json','flex-assets.json'):
            (self.root/name).write_text(json.dumps([legacy]))
        subprocess.run(['git','add','.'],cwd=self.root,check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid',
                        'commit','-qm','legacy major-zero release'],cwd=self.root,check=True)
        for version in ('0.28.0', '1.23.0', '1.23.1', '12.1.10'):
            with self.subTest(version=version):
                result=self.run_check(json.dumps([dict(self.new,version=version),legacy]))
                self.assertEqual(result.returncode,0,result.stderr)

    def test_highlight(self):
        self.new.update(version='highlight-training-2026',highlight=True,title='Training')
        self.assertEqual(self.run_check().returncode,0)

    def test_edit_to_shadowed_duplicate_value_fails(self):
        for shadowed, replacement in (('"earlier"', '"edited"'),
                                      ('{"value":"earlier","value":"kept"}', '{"value":"edited","value":"kept"}'),
                                      ('true', '1')):
            with self.subTest(shadowed=shadowed):
                raw='[{"version":"1.22.0","date":"2026-10-29","notes":[],"pinned":{"flag":' + shadowed + ',"flag":"effective","message":"Hello"}}]'
                for name in ('flex-enterprise.json','flex-assets.json'):
                    (self.root/name).write_text(raw)
                subprocess.run(['git','add','.'],cwd=self.root,check=True)
                subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid',
                                'commit','-qm','historical duplicate values'],cwd=self.root,check=True)
                unchanged=self.run_check(raw)
                self.assertEqual(unchanged.returncode,0,unchanged.stderr)
                reordered=self.run_check(raw.replace('"version":"1.22.0","date":"2026-10-29"',
                                                    '"date":"2026-10-29","version":"1.22.0"'))
                self.assertEqual(reordered.returncode,0,reordered.stderr)
                edited=self.run_check(raw.replace(shadowed,replacement,1))
                self.assertNotEqual(edited.returncode,0,edited.stdout)
                self.assertIn('duplicate key $.pinned.flag',edited.stderr)

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
