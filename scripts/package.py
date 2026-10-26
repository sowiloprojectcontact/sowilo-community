#!/usr/bin/env python3
"""Build a source preview using an explicit allowlist; never bundle user data."""
from pathlib import Path
import hashlib
import tarfile

ROOT = Path(__file__).resolve().parent.parent
FILES = ('main.py', 'sowilo_data.py', 'sowilo_mini.py', 'launch.sh', 'install.sh',
         'requirements.txt', 'requirements-vault.txt', 'requirements-dev.txt',
         'README.md', 'CHANGELOG.md', '.gitignore')
DIRECTORIES = ('community', 'modules', 'tests', 'examples', 'docs', 'scripts', '.github', 'assets')
ALLOWED_SUFFIXES = {'.py', '.md', '.json', '.txt', '.yml', '.pdf', '.docx', '.svg'}
LEGAL_FILENAMES = {'LICENSE', 'COPYING', 'NOTICE', 'THIRD_PARTY_NOTICES'}


def build():
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    archive = destination / 'sowilo-community-1.0.0-preview.tar.gz'
    files = [ROOT / name for name in FILES]
    files.extend(ROOT / name for name in LEGAL_FILENAMES if (ROOT / name).is_file())
    for directory in DIRECTORIES:
        files.extend(p for p in (ROOT/directory).rglob('*')
                     if p.is_file() and not p.is_symlink()
                     and '__pycache__' not in p.parts
                     and (p.suffix in ALLOWED_SUFFIXES or p.name in LEGAL_FILENAMES)
                     and p.name not in ('config.json', 'credentials.json', 'token.json')
                     and not p.name.startswith(('credentials', '.env'))
                     and not (p.suffix == '.json' and 'token' in p.name.lower()))
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('Unsafe archive input')
    with tarfile.open(archive, 'w:gz') as stream:
        for path in sorted(set(files)):
            stream.add(path, arcname=str(Path('Sowilo-Community-V1')/path.relative_to(ROOT)), recursive=False)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix+'.sha256').write_text(checksum+'  '+archive.name+'\n')
    print(f'{archive.name} : {archive.stat().st_size:,} octets, {len(set(files))} fichiers')
    return archive


if __name__ == '__main__':build()
