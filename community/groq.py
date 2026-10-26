"""Client Groq sans SDK ; erreurs affichables sans exposer la clé."""
import json
import socket
from urllib import error, request

BASE_URL = "https://api.groq.com/openai/v1"


class GroqError(Exception):
    pass


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Ne jamais transmettre Authorization à une redirection.


class GroqClient:
    def __init__(self, api_key, model, timeout=35):
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.timeout = timeout
        self.opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
        if not self.api_key or any(c.isspace() for c in self.api_key) or not self.api_key.isascii() or len(self.api_key) > 4096:
            raise GroqError("La clé API est vide ou contient des caractères invalides.")
        if not self.model or len(self.model) > 200 or any(c.isspace() for c in self.model):
            raise GroqError("Indiquez un modèle Groq.")

    def _request(self, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        req = request.Request(BASE_URL + path, data=body, headers={
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json", "User-Agent": "Sowilo-Community/1.0",
        })
        try:
            with self.opener.open(req, timeout=self.timeout) as response:
                data = response.read(4 * 1024 * 1024 + 1)
            if len(data) > 4 * 1024 * 1024:
                raise GroqError("La réponse Groq est trop volumineuse.")
            return json.loads(data)
        except error.HTTPError as exc:
            messages = {400: "Requête refusée : vérifiez le modèle ou réduisez la conversation.",
                        401: "Clé API Groq invalide.", 403: "Accès Groq refusé.",
                        404: "Modèle ou ressource Groq indisponible.",
                        413: "Conversation trop volumineuse. Créez une nouvelle conversation.",
                        429: "Limite Groq atteinte. Réessayez plus tard."}
            raise GroqError(messages.get(exc.code, f"Service Groq indisponible (HTTP {exc.code}).")) from None
        except (error.URLError, TimeoutError, socket.timeout, OSError):
            raise GroqError("Connexion Groq impossible ou délai dépassé. Vérifiez votre réseau.") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise GroqError("Réponse Groq illisible.") from None

    def validate(self):
        data = self._request("/models")
        if not isinstance(data, dict) or not isinstance(data.get("data"), list):
            raise GroqError("Liste des modèles Groq invalide.")
        models = {item.get("id") for item in data["data"] if isinstance(item, dict)}
        if self.model not in models:
            raise GroqError("Ce modèle n'est pas disponible pour cette clé Groq.")
        return True

    def complete(self, messages):
        data = self._request("/chat/completions", {
            "model": self.model, "messages": messages, "stream": False,
            "max_completion_tokens": 2048,
        })
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise GroqError("Réponse Groq sans message exploitable.") from None
        if not isinstance(content, str) or not content.strip():
            raise GroqError("Groq a renvoyé un message vide.")
        return content
