import importlib.util
from pathlib import Path
import tempfile
import unittest


class DesktopTests(unittest.TestCase):
    def test_desktop_install_uses_current_path_and_refuses_overwrite(self):
        path=Path(__file__).resolve().parent.parent/'scripts/install_desktop.py'
        spec=importlib.util.spec_from_file_location('community_desktop_installer',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix='community desktop ') as d:
            root=Path(d);app=root/'My Sowilo 100%';app.mkdir();(app/'launch.sh').write_text('#!/bin/sh\n')
            target=module.install(app,root/'xdg')
            text=target.read_text()
            self.assertIn('100%%',text)
            self.assertIn('Terminal=false',text)
            self.assertNotIn('sudo',text)
            with self.assertRaises(FileExistsError):module.install(app,root/'xdg')
