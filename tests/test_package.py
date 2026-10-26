"""Verify the deliverable contains legal notices and excludes local data."""
import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


class PackageTests(unittest.TestCase):
    def test_archive_preserves_notices_and_excludes_local_data(self):
        root = Path(__file__).resolve().parent.parent
        spec = importlib.util.spec_from_file_location('community_package', root / 'scripts/package.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in module.FILES:
                (fixture / name).write_text('source fixture\n')
            for name in module.DIRECTORIES:
                (fixture / name).mkdir()
            included = ['LICENSE', 'THIRD_PARTY_NOTICES', 'docs/licences/vendor/LICENSE',
                        'docs/licences/vendor/NOTICE', 'community/app.py']
            excluded = ['community/config.json', 'docs/credentials.json', 'docs/token.json',
                        'docs/backup.sqlite3', '.venv/private.py', 'community/__pycache__/cache.py']
            for name in included + excluded:
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('fixture\n')
            (fixture / 'docs/link.txt').symlink_to(fixture / 'community/config.json')
            with patch.object(module, 'ROOT', fixture):
                archive = module.build()
            with tarfile.open(archive) as stream:
                names = {str(Path(name).relative_to('Sowilo-Community-V1')) for name in stream.getnames()}
            self.assertTrue(set(included).issubset(names))
            self.assertFalse(set(excluded) & names)
            self.assertNotIn('docs/link.txt', names)
