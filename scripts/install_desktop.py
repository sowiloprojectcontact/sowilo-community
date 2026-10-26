#!/usr/bin/env python3
"""Install a user desktop launcher only on explicit request, without sudo."""
import os
from pathlib import Path


def install(app_dir, data_home=None):
    app_dir=Path(app_dir).resolve()
    launcher=app_dir/'launch.sh'
    if not launcher.is_file() or '\n' in str(launcher) or '\r' in str(launcher):
        raise ValueError('Dossier application invalide.')
    value=data_home if data_home is not None else os.environ.get('XDG_DATA_HOME','')
    base=Path(value) if value and Path(value).is_absolute() else Path.home()/'.local/share'
    target_dir=base/'applications'
    target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/'sowilo-community.desktop'
    # Desktop Exec quoting is distinct from shell quoting. No shell is involved.
    escaped=str(launcher).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')
    icon=app_dir/'assets/sowilo.svg'
    icon_value=str(icon) if icon.is_file() else 'applications-office'
    content='\n'.join(['[Desktop Entry]','Type=Application','Name=Sowilo Community',
        'Comment=Notes, tâches, documents et assistant IA',f'Exec="{escaped}"',
        f'Icon={icon_value}','Terminal=false','Categories=Office;Utility;',''])
    with target.open('x',encoding='utf-8') as stream:stream.write(content)
    target.chmod(0o700)
    return target


if __name__=='__main__':
    try:
        print(install(Path(__file__).resolve().parent.parent))
    except (OSError,ValueError):
        raise SystemExit('Lanceur non installé : un lanceur existe déjà ou le dossier est inaccessible.')
