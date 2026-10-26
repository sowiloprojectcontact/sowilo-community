"""Tests non graphiques : python -m unittest -v test_sowilo."""
import sqlite3
import importlib.util
import os
import queue
import time
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import tkinter as tk

from sowilo_data import MAX_TEXT_BYTES, StorageError, Store, search_text, summarize_text, extract_text, read_text_file
from sowilo_mini import SowiloMini


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.path = Path(self.directory.name) / "data.sqlite3"
        self.store = Store(self.path)

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def test_note_lifecycle_and_reopening(self):
        note_id = self.store.save_note("  Idées  ", "Bonjour 🌞\nDeuxième ligne")
        self.assertEqual(self.store.notes()[0]["title"], "Idées")
        self.store.save_note("Titre modifié", "Contenu modifié", note_id, expected_revision=1)
        self.store.close()
        self.store = Store(self.path)
        note = self.store.notes()[0]
        self.assertEqual((note["id"], note["content"]), (note_id, "Contenu modifié"))
        self.store.delete_note(note_id, expected_revision=2)
        self.assertEqual(self.store.notes(), [])

    def test_tasks_and_stats_persist(self):
        self.store.save_note("Note", "Texte")
        first = self.store.add_task(" Première ")
        second = self.store.add_task("Deuxième")
        self.store.set_task_done(first, True)
        self.assertEqual(self.store.stats(), {"notes": 1, "tasks": 2, "done": 1, "pending": 1})
        self.assertEqual(self.store.tasks()[0]["id"], second)
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual(self.store.stats()["done"], 1)
        self.store.set_task_done(first, False)
        self.store.delete_task(second)
        self.assertEqual(self.store.stats()["pending"], 1)

    def test_validation_and_parameterized_sql(self):
        with self.assertRaises(ValueError):
            self.store.save_note("  ", "content")
        with self.assertRaises(ValueError):
            self.store.add_task("\t")
        with self.assertRaises(ValueError):
            self.store.save_note("Titre", "Texte", 999)
        title = "'); DROP TABLE notes; --"
        self.store.save_note(title, "'quoted'")
        self.assertEqual(self.store.notes()[0]["title"], title)
        self.assertEqual(self.store.stats()["notes"], 1)

    def test_transaction_failure_does_not_change_data(self):
        self.store.connection.execute("PRAGMA query_only = ON")
        with self.assertRaises(sqlite3.Error):
            self.store.add_task("Refusée")
        self.assertEqual(self.store.stats()["tasks"], 0)

    def test_two_connections_detect_edit_and_delete_conflicts(self):
        other = Store(self.path)
        try:
            note_id = self.store.save_note("Note", "v1")
            stale = other.get_note(note_id)
            self.store.save_note("Note", "v2", note_id, expected_revision=1)
            with self.assertRaises(StorageError):
                other.save_note("Note", "écrasement", note_id, stale["revision"])
            with self.assertRaises(StorageError):
                other.delete_note(note_id, stale["revision"])
            self.assertEqual(other.get_note(note_id)["content"], "v2")
            self.store.delete_note(note_id, expected_revision=2)
            replacement = self.store.save_note("Nouvelle", "à conserver")
            self.assertGreater(replacement, note_id)
            with self.assertRaises(StorageError):
                other.save_note("Ancienne", "écrasement", note_id, stale["revision"])
            self.assertEqual(other.get_note(replacement)["content"], "à conserver")
        finally:
            other.close()

    def test_task_ids_and_stale_operations(self):
        task_id = self.store.add_task("A")
        self.store.set_task_done(task_id, True, expected_done=False)
        with self.assertRaises(StorageError):
            self.store.set_task_done(task_id, True, expected_done=False)
        self.store.delete_task(task_id)
        replacement = self.store.add_task("B")
        self.assertGreater(replacement, task_id)
        with self.assertRaises(StorageError):
            self.store.set_task_done(task_id, False)
        with self.assertRaises(StorageError):
            self.store.delete_task(task_id)

    def test_lock_wait_is_short_and_data_unchanged(self):
        other = sqlite3.connect(self.path)
        try:
            other.execute("BEGIN IMMEDIATE")
            start = time.monotonic()
            with self.assertRaises(sqlite3.OperationalError):
                self.store.add_task("Bloquée")
            self.assertLess(time.monotonic() - start, 1.0)
            self.assertEqual(self.store.stats()["tasks"], 0)
        finally:
            other.rollback()
            other.close()

    def test_headers_and_previews_do_not_fetch_full_notes(self):
        for index in range(5):
            self.store.save_note(str(index), "x" * 1000)
        self.assertNotIn("content", self.store.note_headers()[0].keys())
        recent = self.store.recent_notes()
        self.assertEqual(len(recent), 3)
        self.assertTrue(all(len(n["content"]) == 240 for n in recent))
        self.assertEqual(len(self.store.get_note(recent[0]["id"])["content"]), 1000)

    def test_limits_and_oversized_legacy_note(self):
        with self.assertRaises(ValueError):
            self.store.save_note("Titre", "é" * (MAX_TEXT_BYTES // 2 + 1))
        with self.assertRaises(ValueError):
            self.store.add_task("x" * 301)
        with self.assertRaises(ValueError):
            self.store.save_note("x" * 301, "Texte")
        note_id = self.store.save_note("Titre", "Court")
        with self.store.connection:
            self.store.connection.execute("UPDATE notes SET content=? WHERE id=?", ("x" * (MAX_TEXT_BYTES + 1), note_id))
        with self.assertRaises(StorageError):
            self.store.get_note(note_id)

    def legacy_database(self, name, done=0):
        path = Path(self.directory.name) / name
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("INSERT INTO notes VALUES (7, 'Ancienne', 'Texte 🌞', '2026-01-01')")
        db.execute("INSERT INTO tasks VALUES (8, 'Tâche', ?, '2026-01-01')", (done,))
        db.commit()
        db.close()
        return path

    def test_migration_preserves_data_and_is_repeatable(self):
        path = self.legacy_database("legacy.sqlite3")
        migrated = Store(path)
        try:
            self.assertEqual(migrated.get_note(7)["content"], "Texte 🌞")
            self.assertEqual(migrated.get_note(7)["revision"], 1)
            self.assertEqual(migrated.tasks()[0]["id"], 8)
            self.assertEqual(migrated.connection.execute("PRAGMA user_version").fetchone()[0], 1)
            migrated.delete_note(7, 1)
            self.assertGreater(migrated.save_note("Nouvelle", "Texte"), 7)
        finally:
            migrated.close()
        migrated = Store(path)
        migrated.close()

    def test_failed_migration_rolls_back_original_tables(self):
        path = self.legacy_database("invalid.sqlite3", done=2)
        with self.assertRaises(sqlite3.IntegrityError):
            Store(path)
        db = sqlite3.connect(path)
        try:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT done FROM tasks").fetchone()[0], 2)
            self.assertNotIn("revision", [r[1] for r in db.execute("PRAGMA table_info(notes)")])
            self.assertEqual(db.execute("SELECT content FROM notes").fetchone()[0], "Texte 🌞")
        finally:
            db.close()

    def test_incompatible_schema_and_future_version_are_unchanged(self):
        path = Path(self.directory.name) / "incompatible.sqlite3"
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE notes(id INTEGER PRIMARY KEY, title TEXT)")
        db.commit()
        db.close()
        with self.assertRaises(StorageError):
            Store(path)
        db = sqlite3.connect(path)
        try:
            self.assertEqual([r[1] for r in db.execute("PRAGMA table_info(notes)")], ["id", "title"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='tasks'").fetchone()[0], 0)
        finally:
            db.close()
        self.store.connection.execute("PRAGMA user_version = 99")
        with self.assertRaises(StorageError):
            Store(self.path)
        self.assertEqual(self.store.connection.execute("PRAGMA user_version").fetchone()[0], 99)


class TextTests(unittest.TestCase):
    def test_search_case_boundaries_and_literal_input(self):
        self.assertIn("2 occurrence(s)", search_text("chat CHAT château", "chat"))
        self.assertIn("1 occurrence(s)", search_text("a+b aab", "a+b"))
        self.assertIn("0 occurrence(s)", search_text("bonjour", "absent"))
        with self.assertRaises(ValueError):
            search_text("Texte", " ")

    def test_summary(self):
        self.assertEqual(summarize_text(" Une.\n Deux ! Trois ? Quatre."), "Une. Deux ! Trois ?")
        self.assertEqual(summarize_text(""), "")

    def test_extraction_and_fallback(self):
        result = extract_text("https://example.org\na@exemple.fr\n2026-10-06\n- Faire un test\nhttps://example.org")
        for section in ("Liens", "Adresses e-mail", "Dates", "Éléments de liste"):
            self.assertIn(section, result)
        self.assertEqual(result.count("https://example.org"), 1)
        self.assertEqual(extract_text(" a \n\n b "), "Lignes non vides\na\nb")

    def test_selection_takes_priority_without_a_window(self):
        editor = Mock()
        editor.get.return_value = "sélection"
        app = SimpleNamespace(source_editor=editor)
        self.assertEqual(SowiloMini.get_text(app), "sélection")
        editor.get.side_effect = [tk.TclError("no selection"), "tout le contenu"]
        self.assertEqual(SowiloMini.get_text(app), "tout le contenu")

    def test_task_source_selected_or_all(self):
        app = SimpleNamespace(source_editor=None, page="Tâches", tasks_list=Mock(),
                              task_rows=[{"title": "A", "done": False}, {"title": "B", "done": True}])
        app.tasks_list.curselection.return_value = (1,)
        self.assertEqual(SowiloMini.get_text(app), "Terminée : B")
        app.tasks_list.curselection.return_value = ()
        self.assertEqual(SowiloMini.get_text(app), "À faire : A\nTerminée : B")


class FileTests(unittest.TestCase):
    def test_valid_files_and_rejections(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "note.md"
            path.write_text("# Idée 🌞", encoding="utf-8-sig")
            self.assertEqual(read_text_file(path), "# Idée 🌞")
            path.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                read_text_file(path)
            path.write_bytes(b"a\x00b")
            with self.assertRaisesRegex(ValueError, "texte"):
                read_text_file(path)
            path.write_bytes(b"a" * (2 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "2 Mo"):
                read_text_file(path)
            with self.assertRaises(ValueError):
                read_text_file(Path(directory) / "image.png")
            with self.assertRaises(OSError):
                read_text_file(Path(directory) / "absent.txt")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Tubes nommés non disponibles")
    def test_fifo_is_rejected_before_opening(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "pipe.txt"
            os.mkfifo(path)
            with patch("sowilo_data.os.open", side_effect=AssertionError("Ouverture bloquante")):
                with self.assertRaisesRegex(ValueError, "ordinaire"):
                    read_text_file(path)

    def test_directory_with_text_extension_is_rejected(self):
        with tempfile.TemporaryDirectory(suffix=".txt", dir=Path(__file__).parent) as directory:
            with self.assertRaisesRegex(ValueError, "ordinaire"):
                read_text_file(directory)


class InterfaceLogicTests(unittest.TestCase):
    def test_unsaved_note_cancel_discard_and_save(self):
        app = SimpleNamespace(page="Notes", note_snapshot=("Ancien", "Texte"),
                              note_values=Mock(return_value=("Nouveau", "Texte")),
                              save_note=Mock(return_value=True))
        with patch("sowilo_mini.messagebox.askyesnocancel", return_value=None):
            self.assertFalse(SowiloMini.leave_note(app))
        with patch("sowilo_mini.messagebox.askyesnocancel", return_value=False):
            self.assertTrue(SowiloMini.leave_note(app))
        app.save_note.assert_not_called()
        with patch("sowilo_mini.messagebox.askyesnocancel", return_value=True):
            self.assertTrue(SowiloMini.leave_note(app))
        app.save_note.assert_called_once()
        app.save_note.return_value = False
        with patch("sowilo_mini.messagebox.askyesnocancel", return_value=True):
            self.assertFalse(SowiloMini.leave_note(app))

    def test_storage_errors_hide_technical_details(self):
        action = Mock(side_effect=sqlite3.OperationalError("secret technical path"))
        with patch("sowilo_mini.messagebox.showerror") as dialog:
            self.assertEqual(SowiloMini.run_data(object(), action), (False, None))
        self.assertNotIn("secret technical path", str(dialog.call_args))

    def test_import_has_no_window_storage_or_input_side_effect(self):
        # Tests isolés : aucune hypothèse sur la présence d'une base réelle.
        with patch("tkinter.Tk.__init__", side_effect=AssertionError("Fenêtre créée")), \
             patch("sqlite3.connect", side_effect=AssertionError("Base ouverte")), \
             patch("builtins.input", side_effect=AssertionError("Entrée demandée")):
            for filename in ("sowilo_mini.py", "main.py"):
                spec = importlib.util.spec_from_file_location("isolated_import", Path(__file__).resolve().parent.parent / filename)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

    def test_note_restore_loads_before_selecting(self):
        note = {"id": 42, "title": "Titre", "content": "Texte", "revision": 3}
        calls = []
        app = SimpleNamespace(note_id=42, store=SimpleNamespace(get_note=lambda i: note),
                              run_data=lambda action: (True, action()))
        app.load_note = lambda value: calls.append(("load", value))
        app.refresh_notes = lambda: calls.append(("refresh", None))
        SowiloMini.restore_active_note(app)
        self.assertEqual(calls, [("load", None), ("load", note), ("refresh", None)])

    def test_select_note_fetches_current_content_instead_of_cached_header(self):
        fresh = {"id": 7, "title": "Titre", "content": "À jour", "revision": 2}
        app = SimpleNamespace(notes_list=Mock(), note_rows=[{"id": 7, "title": "Titre"}], note_id=None,
                              store=SimpleNamespace(get_note=Mock(return_value=fresh)),
                              run_data=lambda action: (True, action()), leave_note=lambda: True,
                              load_note=Mock(), refresh_notes=Mock())
        app.notes_list.curselection.return_value = (0,)
        SowiloMini.select_note(app)
        app.load_note.assert_called_once_with(fresh)

    def test_task_view_reuses_draft_variable(self):
        draft = Mock()
        draft.get.return_value = "Brouillon conservé"
        app = SimpleNamespace(content=Mock(), BG="#14111e", task_title=draft,
                              entry=Mock(return_value=Mock()), button=Mock(return_value=Mock()),
                              listbox=Mock(return_value=Mock()), refresh_tasks=Mock(),
                              add_task=Mock(), toggle_task=Mock(), delete_task=Mock(), task_toggle_event=Mock())
        with patch("sowilo_mini.tk.Frame", return_value=Mock()), \
             patch("sowilo_mini.tk.StringVar", side_effect=AssertionError("Brouillon remplacé")):
            SowiloMini.build_tasks(app)
            SowiloMini.build_tasks(app)
        self.assertIs(app.task_title, draft)
        self.assertEqual(app.task_title.get(), "Brouillon conservé")

    def test_save_uses_revision_and_reports_refresh_failure(self):
        app = SimpleNamespace(note_id=7, note_revision=3, note_title=Mock(),
                              note_values=lambda: (" Titre ", "Brouillon"),
                              store=SimpleNamespace(save_note=Mock(return_value=7)),
                              run_data=lambda action: (True, action()), refresh_notes=lambda: False,
                              status=Mock())
        app.refreshed_status = lambda ok, message: SowiloMini.refreshed_status(app, ok, message)
        self.assertTrue(SowiloMini.save_note(app))
        app.store.save_note.assert_called_once_with(" Titre ", "Brouillon", 7, 3)
        self.assertEqual(app.note_revision, 4)
        self.assertIn("Liste non actualisée", app.status.set.call_args[0][0])

    def test_conflict_keeps_editor_and_snapshot_and_copy_is_available(self):
        snapshot = ("Titre", "Original")
        app = SimpleNamespace(note_id=7, note_revision=1, note_title=Mock(),
                              note_values=lambda: ("Titre", "Brouillon"), note_snapshot=snapshot,
                              store=SimpleNamespace(save_note=Mock()), run_data=lambda action: (False, None),
                              refresh_notes=Mock(), refreshed_status=Mock())
        self.assertFalse(SowiloMini.save_note(app))
        self.assertEqual(app.note_snapshot, snapshot)
        self.assertEqual(app.note_revision, 1)
        app.refresh_notes.assert_not_called()
        app.run_data = lambda action: (True, action())
        app.store.save_note.return_value = 8
        self.assertTrue(SowiloMini.save_note(app, as_copy=True))
        app.store.save_note.assert_called_once_with("Titre", "Brouillon", None, None)
        self.assertEqual((app.note_id, app.note_revision), (8, 1))

    def test_refresh_failure_preserves_previous_list(self):
        app = SimpleNamespace(store=SimpleNamespace(note_headers=Mock()),
                              run_data=lambda action: (False, None), status=Mock(),
                              notes_list=Mock(), note_rows=[{"id": 1}], sync_note_selection=Mock())
        self.assertFalse(SowiloMini.refresh_notes(app))
        app.notes_list.delete.assert_not_called()
        self.assertEqual(app.note_rows, [{"id": 1}])

    def test_task_selection_survives_reordering(self):
        app = SimpleNamespace(tasks_list=Mock(), task_rows=[{"id": 1, "done": 0, "title": "A"}],
                              store=SimpleNamespace(tasks=Mock()), MUTED="#b7a9cd", status=Mock(),
                              run_data=lambda action: (True, [{"id": 2, "done": 0, "title": "B"}, {"id": 1, "done": 1, "title": "A"}]))
        app.tasks_list.curselection.return_value = (0,)
        self.assertTrue(SowiloMini.refresh_tasks(app))
        app.tasks_list.selection_set.assert_called_once_with(1)

    def test_file_worker_reports_content_or_safe_error(self):
        results = queue.Queue()
        with patch("sowilo_mini.read_text_file", return_value="Contenu"):
            SowiloMini.read_file_job("test.txt", results)
        self.assertEqual(results.get_nowait(), ("test.txt", "Contenu", None))
        with patch("sowilo_mini.read_text_file", side_effect=OSError("technical secret")):
            SowiloMini.read_file_job("test.txt", results)
        result = results.get_nowait()
        self.assertIsNone(result[1])
        self.assertNotIn("technical secret", result[2])

    def test_file_poll_does_not_touch_destroyed_file_view(self):
        results = queue.Queue()
        results.put(("note.txt", "Contenu", None))
        app = SimpleNamespace(file_jobs=results, file_busy=True, page="Notes", status=Mock())
        SowiloMini.poll_file_job(app)
        self.assertFalse(app.file_busy)
        self.assertEqual(app.file_content, "Contenu")

    def test_file_poll_reschedules_without_waiting(self):
        app = SimpleNamespace(file_jobs=queue.Queue(), after=Mock(), poll_file_job=Mock())
        SowiloMini.poll_file_job(app)
        app.after.assert_called_once_with(50, app.poll_file_job)

    def test_note_selection_matches_editor_even_after_failed_refresh(self):
        app = SimpleNamespace(notes_list=Mock(), note_rows=[{"id": 1}, {"id": 2}], note_id=1)
        SowiloMini.sync_note_selection(app)
        app.notes_list.selection_clear.assert_called_once_with(0, "end")
        app.notes_list.selection_set.assert_called_once_with(0)
        app.note_id = None
        app.notes_list.reset_mock()
        SowiloMini.sync_note_selection(app)
        app.notes_list.selection_set.assert_not_called()

    def test_task_event_stops_class_binding_after_reordering(self):
        app = SimpleNamespace(toggle_task=Mock())
        self.assertEqual(SowiloMini.task_toggle_event(app), "break")
        app.toggle_task.assert_called_once()

    def test_open_file_starts_daemon_job_and_returns_without_reading(self):
        app = SimpleNamespace(file_busy=False, file_jobs=queue.Queue(), status=Mock(),
                              read_file_job=Mock(), after=Mock(), poll_file_job=Mock())
        with patch("sowilo_mini.filedialog.askopenfilename", return_value="note.txt"), \
             patch("sowilo_mini.threading.Thread") as thread, \
             patch("sowilo_mini.read_text_file", side_effect=AssertionError("Lecture dans le fil graphique")):
            SowiloMini.open_file(app)
        self.assertTrue(app.file_busy)
        self.assertTrue(thread.call_args.kwargs["daemon"])
        thread.return_value.start.assert_called_once()
        app.after.assert_called_once_with(50, app.poll_file_job)

    def test_second_file_open_does_not_show_dialog_while_busy(self):
        app = SimpleNamespace(file_busy=True, status=Mock())
        with patch("sowilo_mini.filedialog.askopenfilename") as dialog:
            SowiloMini.open_file(app)
        dialog.assert_not_called()


if __name__ == "__main__":
    unittest.main()
