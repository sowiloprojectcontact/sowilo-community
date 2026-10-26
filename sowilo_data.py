"""Stockage et outils de texte de Sowilo Mini, sans dépendance graphique."""

from pathlib import Path
import re
import os
import stat
import sqlite3


MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_TITLE = 300


class StorageError(ValueError):
    """Erreur de stockage dont le message peut être présenté à l'utilisateur."""


class Store:
    SCHEMA_VERSION = 1

    def __init__(self, path):
        # Une attente courte évite de figer la fenêtre en cas de verrou externe.
        self.connection = sqlite3.connect(path, timeout=0.15)
        self.connection.row_factory = sqlite3.Row
        try:
            self._initialize()
        except (sqlite3.Error, StorageError):
            self.connection.close()
            raise

    def _initialize(self):
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, self.SCHEMA_VERSION):
                raise StorageError("Cette base utilise une version non prise en charge. Conservez-la et ouvrez-la avec une version compatible de Sowilo Mini.")
            tables = {r[0] for r in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            if not tables:
                self._create_tables()
            else:
                if tables != {"notes", "tasks"}:
                    raise StorageError("Le format de la base locale n’est pas compatible. Vos données n’ont pas été modifiées.")
                self._validate_columns(version)
                if version == 0:
                    # Migration atomique du format original, en conservant IDs et données.
                    self.connection.execute("ALTER TABLE notes RENAME TO legacy_notes")
                    self.connection.execute("ALTER TABLE tasks RENAME TO legacy_tasks")
                    self._create_tables()
                    self.connection.execute("INSERT INTO notes(id,title,content,updated_at) SELECT id,title,content,updated_at FROM legacy_notes")
                    self.connection.execute("INSERT INTO tasks(id,title,done,created_at) SELECT id,title,done,created_at FROM legacy_tasks")
                    self.connection.execute("DROP TABLE legacy_notes")
                    self.connection.execute("DROP TABLE legacy_tasks")
            self._validate_columns(self.SCHEMA_VERSION)
            for table in ("notes", "tasks"):
                sql = self.connection.execute("SELECT sql FROM sqlite_master WHERE name=?", (table,)).fetchone()[0]
                if "AUTOINCREMENT" not in sql.upper():
                    raise StorageError("Le format des identifiants de la base locale n’est pas compatible.")
            self._validate_data()
            self.connection.execute("CREATE INDEX IF NOT EXISTS notes_recent ON notes(updated_at DESC, id DESC)")
            self.connection.execute("CREATE INDEX IF NOT EXISTS tasks_order ON tasks(done, id DESC)")
            self.connection.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION}")
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _create_tables(self):
        self.connection.execute("""CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1))""")
        self.connection.execute("""CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

    def _validate_columns(self, version):
        expected = {"notes": {"id": "INTEGER", "title": "TEXT", "content": "TEXT", "updated_at": "TEXT"},
                    "tasks": {"id": "INTEGER", "title": "TEXT", "done": "INTEGER", "created_at": "TEXT"}}
        if version == 1:
            expected["notes"]["revision"] = "INTEGER"
        for table, columns in expected.items():
            rows = self.connection.execute(f"PRAGMA table_info({table})").fetchall()
            actual = {r["name"]: r["type"].upper() for r in rows}
            if actual != columns or not any(r["name"] == "id" and r["pk"] == 1 for r in rows):
                raise StorageError("Le schéma de la base locale n’est pas compatible. Vos données n’ont pas été modifiées.")
            if any(r["name"] != "id" and not r["notnull"] for r in rows):
                raise StorageError("Les contraintes de la base locale ne sont pas compatibles.")

    def _validate_data(self):
        invalid_notes = self.connection.execute("""SELECT 1 FROM notes WHERE
            typeof(title) != 'text' OR typeof(content) != 'text' OR typeof(updated_at) != 'text'
            OR typeof(revision) != 'integer' OR revision < 1 LIMIT 1""").fetchone()
        invalid_tasks = self.connection.execute("""SELECT 1 FROM tasks WHERE
            typeof(title) != 'text' OR typeof(created_at) != 'text'
            OR typeof(done) != 'integer' OR done NOT IN (0,1) LIMIT 1""").fetchone()
        if invalid_notes or invalid_tasks:
            raise StorageError("La base locale contient des données incompatibles. Conservez-la pour récupérer vos données.")

    def notes(self):
        return self.connection.execute("SELECT * FROM notes ORDER BY updated_at DESC, id DESC").fetchall()

    def note_headers(self):
        return self.connection.execute("SELECT id, title FROM notes ORDER BY updated_at DESC, id DESC").fetchall()

    def recent_notes(self):
        return self.connection.execute("SELECT id, title, substr(content,1,240) AS content FROM notes ORDER BY updated_at DESC, id DESC LIMIT 3").fetchall()

    def get_note(self, note_id):
        note = self.connection.execute("""SELECT id, title, updated_at, revision,
            CASE WHEN length(CAST(content AS BLOB)) <= ? THEN content ELSE NULL END AS content
            FROM notes WHERE id=?""", (MAX_TEXT_BYTES, note_id)).fetchone()
        if note is None:
            raise StorageError("Cette note a été supprimée. Vous pouvez conserver votre texte dans une nouvelle note.")
        if note["content"] is None:
            raise StorageError("Cette note dépasse la limite de 2 Mo et ne peut pas être affichée.")
        return note

    @staticmethod
    def _title(title):
        title = title.strip()
        if not title:
            raise ValueError("Saisissez un titre.")
        if len(title) > MAX_TITLE:
            raise ValueError("Le titre ne doit pas dépasser 300 caractères.")
        return title

    def save_note(self, title, content, note_id=None, expected_revision=None):
        title = self._title(title)
        if len(content.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("La note dépasse la limite de 2 Mo. Réduisez son contenu avant de l’enregistrer.")
        with self.connection:
            if note_id is None:
                return self.connection.execute("INSERT INTO notes(title, content) VALUES (?, ?)", (title, content)).lastrowid
            if expected_revision is None:
                raise StorageError("Rechargez la note avant de l’enregistrer.")
            cursor = self.connection.execute(
                "UPDATE notes SET title=?, content=?, updated_at=CURRENT_TIMESTAMP, revision=revision+1 WHERE id=? AND revision=?",
                (title, content, note_id, expected_revision))
            if not cursor.rowcount:
                raise StorageError("Cette note a été modifiée ou supprimée dans une autre fenêtre. Votre texte est conservé ici. Copiez-le avant de recharger la note ou créez-en une copie.")
        return note_id

    def delete_note(self, note_id, expected_revision=None):
        if expected_revision is None:
            raise StorageError("Rechargez la note avant de la supprimer.")
        with self.connection:
            cursor = self.connection.execute("DELETE FROM notes WHERE id=? AND revision=?", (note_id, expected_revision))
            if not cursor.rowcount:
                raise StorageError("Cette note a été modifiée ou supprimée dans une autre fenêtre. Rechargez-la avant de continuer.")

    def tasks(self):
        return self.connection.execute("SELECT * FROM tasks ORDER BY done, id DESC").fetchall()

    def add_task(self, title):
        title = self._title(title)
        with self.connection:
            return self.connection.execute("INSERT INTO tasks(title) VALUES (?)", (title,)).lastrowid

    def set_task_done(self, task_id, done, expected_done=None):
        with self.connection:
            sql = "UPDATE tasks SET done=? WHERE id=?"
            args = [int(bool(done)), task_id]
            if expected_done is not None:
                sql += " AND done=?"
                args.append(int(bool(expected_done)))
            if not self.connection.execute(sql, args).rowcount:
                raise StorageError("Cette tâche a été modifiée ou supprimée. Actualisez la liste.")

    def delete_task(self, task_id):
        with self.connection:
            if not self.connection.execute("DELETE FROM tasks WHERE id=?", (task_id,)).rowcount:
                raise StorageError("Cette tâche a déjà été supprimée. Actualisez la liste.")

    def stats(self):
        row = self.connection.execute("SELECT (SELECT COUNT(*) FROM notes), COUNT(*), COALESCE(SUM(done), 0) FROM tasks").fetchone()
        notes, tasks, done = row
        return {"notes": notes, "tasks": tasks, "done": done, "pending": tasks - done}

    def close(self):
        self.connection.close()


def search_text(text, query):
    query = query.strip()
    if not query:
        raise ValueError("Saisissez un mot ou une expression à rechercher.")
    matches = re.finditer(r"(?<!\w)" + re.escape(query) + r"(?!\w)",
                              text, flags=re.IGNORECASE)
    snippets = []
    count = 0
    for match in matches:
        count += 1
        if count > 20:
            continue
        excerpt = text[max(0, match.start() - 45):match.end() + 65]
        snippets.append("• " + re.sub(r"\s+", " ", excerpt).strip())
    return f'« {query} » : {count} occurrence(s).\n\n' + "\n".join(snippets)


def summarize_text(text):
    compact = re.sub(r"\s+", " ", text).strip()
    return " ".join(re.split(r"(?<=[.!?…])\s+", compact)[:3])


def extract_text(text):
    """Extrait les coordonnées et les lignes structurées, sans modèle externe."""
    groups = [
        ("Liens", re.findall(r"https?://[^\s<>]+", text)),
        ("Adresses e-mail", re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)),
        ("Dates", re.findall(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)),
        ("Éléments de liste", [line.strip() for line in text.splitlines()
                               if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)]),
    ]
    sections = [name + "\n" + "\n".join(dict.fromkeys(values))
                for name, values in groups if values]
    if sections:
        return "\n\n".join(sections)
    return "Lignes non vides\n" + "\n".join(line.strip() for line in text.splitlines()
                                             if line.strip())


def read_text_file(path):
    path = Path(path)
    if path.suffix.lower() not in {".txt", ".md"}:
        raise ValueError("Choisissez un fichier .txt ou .md.")
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Choisissez un fichier texte ordinaire.")
    # O_NONBLOCK protège aussi contre un remplacement par un tube entre stat et open.
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Choisissez un fichier texte ordinaire.")
        raw = stream.read(MAX_TEXT_BYTES + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Ce fichier dépasse la limite de 2 Mo.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("Ce fichier doit être enregistré en UTF-8.") from None
    if "\x00" in text:
        raise ValueError("Ce fichier ne semble pas contenir du texte.")
    return text
