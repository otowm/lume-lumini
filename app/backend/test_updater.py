import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.backend import updater


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.remote = base / 'upstream'
        self.local = base / 'installed'
        self.home = base / 'home'
        self.home.mkdir()
        self.run_git(base, 'init', '-b', 'main', str(self.remote))
        self.run_git(self.remote, 'config', 'user.name', 'Test')
        self.run_git(self.remote, 'config', 'user.email', 'test@example.invalid')
        (self.remote / 'bin').mkdir()
        for name in updater.SCRIPTS:
            (self.remote / 'bin' / name).write_text('#!/bin/sh\nexit 0\n')
        (self.remote / 'version.txt').write_text('old')
        self.commit('initial')
        self.run_git(base, 'clone', str(self.remote), str(self.local))
        self.before = self.run_git(self.local, 'rev-parse', 'HEAD')
        (self.remote / 'version.txt').write_text('new')
        self.target = self.commit('update')
        for item in [patch.object(updater, 'ROOT', self.local),
                     patch.object(updater, 'REPOSITORY', str(self.remote)),
                     patch.object(updater, 'STATE', base / 'config' / 'updates.json'),
                     patch.object(updater, 'runtime_active', return_value=False),
                     patch.object(updater, 'e_lumini', return_value=True),
                     patch.object(Path, 'home', return_value=self.home)]:
            item.start()
            self.addCleanup(item.stop)
        updater.write_state({'latest':self.target, 'checked_at':9999999999})

    def run_git(self, cwd, *args):
        return subprocess.check_output(['git', '-C', str(cwd), *args], stderr=subprocess.DEVNULL, text=True).strip()

    def commit(self, message):
        self.run_git(self.remote, 'add', '.')
        self.run_git(self.remote, 'commit', '-m', message)
        return self.run_git(self.remote, 'rev-parse', 'HEAD')

    def test_prepare_does_not_change_running_code_then_apply_preserves_user_files(self):
        preference = self.home / 'preferences.conf'
        preference.write_text('my microphone')
        updater.prepare(self.target)
        self.assertEqual(self.run_git(self.local,'rev-parse','HEAD'), self.before)
        self.assertTrue(updater.apply_pending())
        self.assertEqual(self.run_git(self.local,'rev-parse','HEAD'), self.target)
        self.assertEqual(preference.read_text(), 'my microphone')
        self.assertFalse(updater.read_state()['pending'])

    def test_local_edits_are_preserved(self):
        (self.local / 'version.txt').write_text('custom')
        with self.assertRaises(updater.UpdateError):updater.prepare(self.target)
        self.assertEqual((self.local / 'version.txt').read_text(), 'custom')

    def test_active_runtime_defers_installation(self):
        updater.prepare(self.target)
        with patch.object(updater, 'runtime_active', return_value=True):
            self.assertFalse(updater.apply_pending())
        self.assertEqual(self.run_git(self.local,'rev-parse','HEAD'), self.before)
        self.assertEqual(updater.read_state()['pending'],self.target)

    def test_cancel_leaves_current_version_untouched(self):
        updater.prepare(self.target)
        updater.cancel()
        self.assertFalse(updater.apply_pending())
        self.assertEqual(self.run_git(self.local,'rev-parse','HEAD'), self.before)

    def test_switching_to_complete_mode_does_not_install_pending_update(self):
        updater.prepare(self.target)
        with patch.object(updater, 'e_lumini', return_value=False):
            self.assertFalse(updater.apply_pending())
        self.assertEqual(self.run_git(self.local,'rev-parse','HEAD'), self.before)

    def test_new_dependencies_require_installer_before_scheduling(self):
        (self.remote / 'requirements-lumini.txt').write_text('new-package==1')
        target = self.commit('dependencies')
        updater.write_state({'latest':target})
        with self.assertRaisesRegex(updater.UpdateError,'instalador'):updater.prepare(target)
        self.assertFalse(updater.read_state().get('pending'))

    def test_copy_failure_rolls_back_code(self):
        updater.prepare(self.target)
        with patch.object(updater.shutil, 'copyfile', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):updater.apply_pending()
        self.assertEqual(self.run_git(self.local,'rev-parse','HEAD'), self.before)

    def test_offline_keeps_available_version_and_error(self):
        with patch.object(updater.urllib.request, 'urlopen', side_effect=OSError('offline')):
            status = updater.check(force=True)
        self.assertEqual(status['latest'],self.target)
        self.assertIn('Não foi possível', status['error'])

    def test_zip_install_provides_download_link(self):
        with patch.object(updater, 'ROOT', self.home):
            status=updater.check()
        self.assertFalse(status['can_prepare'])
        self.assertIn('ZIP',status['reason'])
        self.assertTrue(status['download_url'].startswith('https://github.com/otowm/'))


class UpdateApiTests(unittest.TestCase):
    def test_recording_rejects_update_before_git_is_called(self):
        from fastapi import HTTPException
        from app.backend import main
        with patch.object(main.mode, 'e_lumini', return_value=True), \
             patch.object(main, 'selective_video_status', return_value={'recording':True}), \
             patch.object(updater, 'prepare') as prepare:
            with self.assertRaises(HTTPException) as error:
                main.prepare_update(main.UpdateRequest(version='a'*40))
            self.assertEqual(error.exception.status_code,409)
            prepare.assert_not_called()
