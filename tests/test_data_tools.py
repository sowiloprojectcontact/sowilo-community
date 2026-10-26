"""Data portability and destructive restore: real temporary databases only."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from community.data_tools import save_backup,read_backup,restore_backup,export_notes,snapshot,MAX_BACKUP_BYTES
from sowilo_data import Store,StorageError


class DataToolsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.store=Store(self.root/'data.sqlite3');self.addCleanup(self.store.close)
        self.note=self.store.save_note('Idée / ../ test','Bonjour 🌞\nDeux lignes')
        self.task=self.store.add_task('Préparer la démo')

    def test_backup_roundtrip_excludes_credentials_and_documents(self):
        path=save_backup(self.store,self.root/'backup.json')
        data=read_backup(path)
        self.assertEqual(data['notes'][0]['content'],'Bonjour 🌞\nDeux lignes')
        self.assertEqual(set(data),{'format','version','created_at','notes','tasks'})
        self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_restore_makes_safety_copy_and_new_ids_protect_stale_window(self):
        payload=snapshot(self.store)
        self.store.save_note('Autre','À conserver dans la copie')
        old_ids={row['id'] for row in self.store.notes()}
        safety=restore_backup(self.store,payload,self.root/'safety')
        self.assertEqual(len(read_backup(safety)['notes']),2)
        self.assertEqual(len(self.store.notes()),1)
        self.assertFalse(old_ids & {row['id'] for row in self.store.notes()})
        with self.assertRaises(StorageError):self.store.save_note('Écrasement','stale',self.note,1)

    def test_invalid_backup_never_changes_current_data(self):
        original=snapshot(self.store)
        for value in ({}, {'format':'sowilo-community-data','version':True,'notes':[],'tasks':[]},
                      {'format':'sowilo-community-data','version':1,'notes':[{'title':'Bad','content':42}],'tasks':[]}):
            with self.assertRaises(ValueError):restore_backup(self.store,value,self.root/'safety')
            self.assertEqual(snapshot(self.store)['notes'],original['notes'])
        self.assertFalse((self.root/'safety').exists())

    def test_restore_rolls_back_if_insert_fails(self):
        payload=snapshot(self.store)
        payload['notes'][0]['title']='Refused'
        self.store.connection.execute("CREATE TRIGGER reject_restore BEFORE INSERT ON notes WHEN NEW.title='Refused' BEGIN SELECT RAISE(ABORT,'refuse'); END")
        with self.assertRaises(sqlite3.IntegrityError):restore_backup(self.store,payload,self.root/'safety')
        self.assertEqual(self.store.get_note(self.note)['title'],'Idée / ../ test')
        self.assertEqual(len(self.store.tasks()),1)
        self.assertEqual(len(list((self.root/'safety').glob('*.json'))),1)

    def test_backup_failure_prevents_destructive_restore(self):
        payload=snapshot(self.store)
        with patch('community.data_tools.atomic_write',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):restore_backup(self.store,payload,self.root/'safety')
        self.assertEqual(self.store.get_note(self.note)['content'],'Bonjour 🌞\nDeux lignes')
        self.assertFalse(self.store.connection.in_transaction)

    def test_export_uses_safe_unique_names_and_never_overwrites(self):
        one=export_notes(self.store,self.root)
        two=export_notes(self.store,self.root)
        self.assertNotEqual(one,two)
        files=list(one.glob('*.md'))
        self.assertEqual(len(files),1)
        self.assertEqual(files[0].parent,one)
        self.assertIn('Bonjour 🌞',files[0].read_text())
        self.assertEqual(files[0].stat().st_mode & 0o777,0o600)

    def test_corrupt_and_oversized_backup_rejected(self):
        bad=self.root/'bad.json';bad.write_text('{broken')
        with self.assertRaises(ValueError):read_backup(bad)
        with bad.open('wb') as stream:stream.truncate(MAX_BACKUP_BYTES+1)
        with self.assertRaises(ValueError):read_backup(bad)

    def test_backup_destination_symlink_does_not_touch_target(self):
        original=self.root/'original';original.write_text('Keep')
        link=self.root/'link';link.symlink_to(original)
        with self.assertRaises(ValueError):save_backup(self.store,link)
        self.assertEqual(original.read_text(),'Keep')

    def test_read_backup_rejects_fifo_and_symlink(self):
        import os
        fifo=self.root/'fifo';os.mkfifo(fifo)
        with self.assertRaises(ValueError):read_backup(fifo)
        valid=save_backup(self.store,self.root/'good.json')
        link=self.root/'link';link.symlink_to(valid)
        with self.assertRaises(OSError):read_backup(link)

    def test_restore_rejects_redirected_safety_directory(self):
        target=self.root/'outside';target.mkdir()
        link=self.root/'safety';link.symlink_to(target,target_is_directory=True)
        with self.assertRaises(ValueError):restore_backup(self.store,snapshot(self.store),link)
        self.assertEqual(list(target.iterdir()),[])
        self.assertEqual(len(self.store.notes()),1)
