import subprocess
import unittest
from test_plugin import ROOT


class ScriptTests(unittest.TestCase):
    def test_obsolete_modes_and_purge_refused(self):
        for script, argument in [('install.sh', '--bundled'), ('install.sh', '--standalone'), ('install.sh', '--symlink'), ('uninstall.sh', '--purge')]:
            with self.subTest(script=script, argument=argument):
                result = subprocess.run(['bash', str(ROOT / script), argument], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)

    def test_help_and_shell_syntax(self):
        for script in ['install.sh', 'uninstall.sh']:
            subprocess.run(['bash', '-n', str(ROOT / script)], check=True)
            result = subprocess.run(['bash', str(ROOT / script), '--help'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn('hermes plugins', result.stdout)
