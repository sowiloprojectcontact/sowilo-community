"""Application-owned paths; no Pro data or configuration fallback."""
from dataclasses import dataclass
import os
from pathlib import Path


class ConfigurationError(Exception):
    """Safe message suitable for display without exception diagnostics."""


def reject_symlinks(path):
    path = Path(path)
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ConfigurationError("Chemin de configuration non sûr : lien symbolique refusé.")


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path
    documents_dir: Path
    config_file: Path

    @classmethod
    def discover(cls):
        home = Path.home()
        def base(variable, fallback):
            value = os.environ.get(variable, "")
            return Path(value) if value and Path(value).is_absolute() else fallback
        config = base("XDG_CONFIG_HOME", home / ".config") / "sowilo-community"
        data = base("XDG_DATA_HOME", home / ".local" / "share") / "sowilo-community"
        return cls(config, data, data / "documents", config / "config.json")

    def ensure(self):
        try:
            for directory in (self.config_dir, self.data_dir, self.documents_dir):
                if not directory.is_absolute():
                    raise ConfigurationError("Chemins de configuration invalides.")
                reject_symlinks(directory)
                directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                reject_symlinks(directory)
                directory.chmod(0o700)
            reject_symlinks(self.config_file)
        except ConfigurationError:
            raise
        except Exception:
            raise ConfigurationError("Impossible de préparer les dossiers de l’application.") from None
