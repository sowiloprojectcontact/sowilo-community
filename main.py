#!/usr/bin/env python3
"""Sowilo Community entry point. Import and diagnostic mode have no side effects."""
import argparse
import importlib
import os
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sowilo Community V1 — Linux")
    parser.add_argument("--check", action="store_true", help="Vérifier les dépendances sans ouvrir de fenêtre ni de données")
    parser.add_argument("--version", action="version", version="Sowilo Community 1.0.0-dev")
    options = parser.parse_args(argv)
    if options.check:
        missing = []
        for name in ("tkinter", "pypdf", "docx", "community.app"):
            try:
                importlib.import_module(name)
            except Exception:
                missing.append(name)
        if missing:
            print("Imports indisponibles : " + ", ".join(missing) + ". Consultez README.md et install.sh.", file=sys.stderr)
            return 1
        print("Sowilo Community : imports disponibles. Aucune clé lue, aucun stockage ouvert, aucun appel réseau.")
        return 0
    os.umask(0o077)
    try:
        import tkinter as tk
        # Probe DISPLAY before creating persistent user storage.
        probe = tk.Tk()
        probe.withdraw()
        probe.destroy()
        from community.paths import AppPaths, reject_symlinks
        from community.config import AppConfig
        from community.app import CommunityApp
        paths = AppPaths.discover()
        paths.ensure()
        reject_symlinks(paths.data_dir / "community.sqlite3")
        config = AppConfig(paths)
        config.load()
        app = CommunityApp(config)
        app.mainloop()
        return 0
    except Exception as error:
        from community.paths import ConfigurationError
        if isinstance(error, ConfigurationError):
            print(str(error), file=sys.stderr)
        else:
            print("Impossible de démarrer Community. Vérifiez Tkinter, les dépendances, l’accès aux données et la session graphique Linux (DISPLAY).", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
