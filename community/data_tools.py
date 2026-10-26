"""Portable data snapshots and Markdown export. No credentials or document copies."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid
from sowilo_data import MAX_TEXT_BYTES, MAX_TITLE

MAX_BACKUP_BYTES = 50 * 1024 * 1024
MAX_ITEMS = 50_000


def atomic_write(path, content):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Sélectionnez un fichier ordinaire, sans lien symbolique.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.sowilo-', delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def snapshot(store):
    # Keep a standalone read coherent, or share the caller's restore transaction.
    connection = store.connection
    own_transaction = not connection.in_transaction
    if own_transaction:
        connection.execute('BEGIN')
    try:
        notes = [dict(row) for row in connection.execute('SELECT title,content,updated_at FROM notes ORDER BY id')]
        tasks = [dict(row) for row in connection.execute('SELECT title,done,created_at FROM tasks ORDER BY id')]
    finally:
        if own_transaction:
            connection.rollback()
    payload = {'format':'sowilo-community-data', 'version':1,
               'created_at':datetime.now(timezone.utc).isoformat(), 'notes':notes, 'tasks':tasks}
    validate_snapshot(payload)
    return payload


def validate_snapshot(payload):
    if not isinstance(payload,dict) or payload.get('format')!='sowilo-community-data' or type(payload.get('version')) is not int or payload['version']!=1:
        raise ValueError("Ce fichier n’est pas une sauvegarde Community compatible.")
    for kind in ('notes','tasks'):
        items=payload.get(kind)
        if not isinstance(items,list) or len(items)>MAX_ITEMS:
            raise ValueError("Sauvegarde trop volumineuse ou invalide.")
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('title'),str) or not item['title'].strip() or len(item['title'])>MAX_TITLE:
                raise ValueError("La sauvegarde contient un titre invalide.")
            timestamp = item.get('updated_at' if kind == 'notes' else 'created_at')
            if timestamp is not None:
                if not isinstance(timestamp, str) or len(timestamp) > 64:
                    raise ValueError("Date de sauvegarde invalide.")
                try:
                    datetime.fromisoformat(timestamp)
                except ValueError:
                    raise ValueError("Date de sauvegarde invalide.") from None
            if kind=='notes':
                if not isinstance(item.get('content'),str) or len(item['content'].encode('utf-8'))>MAX_TEXT_BYTES:
                    raise ValueError("La sauvegarde contient une note invalide ou trop volumineuse.")
            elif type(item.get('done')) is not int or item['done'] not in (0,1):
                raise ValueError("La sauvegarde contient un état de tâche invalide.")
    return payload


def save_backup(store, path):
    raw=json.dumps(snapshot(store),ensure_ascii=False,indent=2).encode('utf-8')
    if len(raw)>MAX_BACKUP_BYTES:
        raise ValueError("La sauvegarde dépasse la limite de 50 Mio.")
    atomic_write(path,raw)
    return Path(path)


def read_backup(path):
    flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
    descriptor=os.open(path,flags)
    with os.fdopen(descriptor,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>MAX_BACKUP_BYTES:
            raise ValueError("Choisissez une sauvegarde ordinaire de 50 Mio maximum.")
        raw=stream.read(MAX_BACKUP_BYTES+1)
    if len(raw)>MAX_BACKUP_BYTES:
        raise ValueError("Sauvegarde trop volumineuse.")
    try:
        payload=json.loads(raw)
    except (ValueError,UnicodeDecodeError,RecursionError):
        raise ValueError("Sauvegarde illisible ; aucune donnée n’a été modifiée.") from None
    return validate_snapshot(payload)


def restore_backup(store, payload, safety_directory):
    # Validate before creating a safety copy or starting any destructive operation.
    validate_snapshot(payload)
    safety_directory=Path(safety_directory)
    if any(path.is_symlink() for path in (safety_directory, *safety_directory.parents)):
        raise ValueError("Le dossier de sécurité ne doit pas être un lien symbolique.")
    safety_directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    safety_directory.chmod(0o700)
    safety=safety_directory/f'avant-restauration-{uuid.uuid4().hex}.json'
    with store.connection:
        store.connection.execute('BEGIN IMMEDIATE')
        save_backup(store,safety)
        store.connection.execute('DELETE FROM notes')
        store.connection.execute('DELETE FROM tasks')
        # Fresh IDs prevent a stale second window from editing restored records.
        for note in payload['notes']:
            store.connection.execute('INSERT INTO notes(title,content,updated_at) VALUES(?,?,COALESCE(?,CURRENT_TIMESTAMP))',(note['title'],note['content'],note.get('updated_at')))
        for task in payload['tasks']:
            store.connection.execute('INSERT INTO tasks(title,done,created_at) VALUES(?,?,COALESCE(?,CURRENT_TIMESTAMP))',(task['title'],task['done'],task.get('created_at')))
    return safety


def markdown(note):
    return ('# '+note['title']+'\n\n'+note['content']+'\n').encode('utf-8')


def export_notes(store, directory):
    notes=snapshot(store)['notes']
    if not notes:
        raise ValueError("Aucune note à exporter.")
    destination=Path(directory)/('sowilo-notes-'+uuid.uuid4().hex[:10])
    destination.mkdir(mode=0o700)
    for index,note in enumerate(notes,1):
        name=re.sub(r'[^\w-]+','-',note['title'],flags=re.UNICODE).strip('-')[:60] or 'note'
        atomic_write(destination/f'{index:04d}-{name}.md',markdown(note))
    return destination
