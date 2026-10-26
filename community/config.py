"""Independent roots configuration and optional OS-vault Groq credentials."""
import json
import os
from pathlib import Path
import tempfile

from .paths import ConfigurationError, reject_symlinks

_SERVICE = "Sowilo Community"
_ACCOUNT = "groq_api_key"


def _secure_vault():
    try:
        import keyring
        backend = keyring.get_keyring()
        module = type(backend).__module__
        # Reject plaintext, fail, null, arbitrary plugins and composite chainers.
        if module not in ("keyring.backends.SecretService", "keyring.backends.kwallet"):
            raise ValueError
        if backend.priority <= 0:
            raise ValueError
        return backend
    except Exception:
        raise ConfigurationError("Coffre sécurisé indisponible ; la clé reste uniquement en mémoire.") from None


class AppConfig:
    def __init__(self, paths):
        self.paths = paths
        self._roots = (paths.documents_dir.resolve(),)
        self._key = ""
        self.model = "openai/gpt-oss-20b"
        self.guide_step = 0
        self.guide_dismissed = False
        self.guide_completed = False
        self.vault_enabled = False

    @property
    def roots(self):
        return self._roots

    def _root(self, path):
        try:
            candidate = Path(path).expanduser()
            if not candidate.is_absolute():
                raise ValueError
            root = candidate.resolve(strict=True)
            if not root.is_dir():
                raise ValueError
            return root
        except Exception:
            raise ConfigurationError("Dossier introuvable ou inaccessible.") from None

    def load(self):
        try:
            reject_symlinks(self.paths.config_file)
            if not self.paths.config_file.exists():
                return
            if self.paths.config_file.stat().st_size > 1024 * 1024:
                raise ValueError
            payload = json.loads(self.paths.config_file.read_text(encoding="utf-8"))
            model = payload.get("model", "openai/gpt-oss-20b")
            step = payload.get("guide_step", 0)
            if not isinstance(model, str) or not model.strip() or len(model) > 200 or any(c.isspace() for c in model):
                raise ValueError
            if type(step) is not int or not 0 <= step <= 3:
                raise ValueError
            if any(type(payload.get(k, False)) is not bool for k in ("guide_dismissed", "guide_completed")):
                raise ValueError
            self.model = model
            self.guide_step = step
            self.guide_dismissed = payload.get("guide_dismissed", False)
            self.guide_completed = payload.get("guide_completed", False)
            roots = payload.get("roots", [])
            if not isinstance(roots, list) or any(not isinstance(p, str) for p in roots):
                raise ValueError
            valid = [self.paths.documents_dir.resolve()]
            for item in roots:
                try:
                    root = self._root(item)
                    if root != Path(item):
                        continue
                    if root not in valid:
                        valid.append(root)
                except ConfigurationError:
                    continue
            self._roots = tuple(valid)
        except ConfigurationError:
            raise
        except Exception:
            raise ConfigurationError("Configuration illisible ou invalide.") from None

    def save(self):
        temporary = None
        try:
            self.paths.ensure()
            reject_symlinks(self.paths.config_file)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.paths.config_dir,
                                             prefix=".config-", delete=False) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), 0o600)
                json.dump({"roots": [str(p) for p in self.roots], "provider": "groq",
                           "model": self.model, "guide_step": self.guide_step,
                           "guide_dismissed": self.guide_dismissed,
                           "guide_completed": self.guide_completed}, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.paths.config_file)
        except ConfigurationError:
            raise
        except Exception:
            raise ConfigurationError("Impossible d’enregistrer la configuration.") from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def authorize_root(self, path):
        root = self._root(path)
        previous = self._roots
        if root not in previous:
            self._roots += (root,)
            try:
                self.save()
            except Exception:
                self._roots = previous
                raise
        return root

    def forget_root(self, path):
        try:
            candidate = Path(path).expanduser()
            if not candidate.is_absolute():
                raise ValueError
            # Keep the original canonical identity even when deleted or replaced.
            root = candidate.absolute()
            if root not in self._roots:
                root = candidate.resolve(strict=False)
        except Exception:
            raise ConfigurationError("Dossier autorisé invalide.") from None
        if root == self.paths.documents_dir.resolve():
            raise ConfigurationError("Le dossier Documents de l’application doit rester autorisé.")
        previous = self._roots
        self._roots = tuple(item for item in previous if item != root)
        try:
            self.save()
        except Exception:
            self._roots = previous
            raise

    def set_api_key(self, key, persist=False):
        if not isinstance(key, str) or not key.strip() or "\n" in key or "\r" in key:
            raise ConfigurationError("Clé Groq invalide.")
        self._key = key.strip()
        if persist:
            try:
                _secure_vault().set_password(_SERVICE, _ACCOUNT, self._key)
            except Exception:
                raise ConfigurationError("Coffre sécurisé indisponible ; la clé reste uniquement en mémoire.") from None

    def get_api_key(self):
        if self._key:
            return self._key
        if not self.vault_enabled:
            return ""
        try:
            result = _secure_vault().get_password(_SERVICE, _ACCOUNT)
            return result if isinstance(result, str) else ""
        except Exception:
            return ""

    def has_api_key(self):
        return bool(self.get_api_key())

    def clear_api_key(self):
        self.forget_memory()
        try:
            vault = _secure_vault()
        except ConfigurationError:
            raise ConfigurationError("Clé mémoire effacée ; suppression du coffre indisponible. Vérifiez le coffre du système.") from None
        try:
            if vault.get_password(_SERVICE, _ACCOUNT):
                vault.delete_password(_SERVICE, _ACCOUNT)
        except Exception:
            raise ConfigurationError("Clé mémoire effacée ; impossible de supprimer la clé du coffre.") from None

    def use_vault(self):
        try:
            result = _secure_vault().get_password(_SERVICE, _ACCOUNT)
            if not isinstance(result, str) or not result.strip():
                raise ConfigurationError("Aucune clé Community enregistrée dans le coffre.")
        except ConfigurationError:
            raise
        except Exception:
            raise ConfigurationError("Impossible de charger la clé Community du coffre sécurisé.") from None
        self._key = result
        self.vault_enabled = True

    def forget_memory(self):
        self._key = ""
        self.vault_enabled = False
