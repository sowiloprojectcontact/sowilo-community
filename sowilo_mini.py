"""Sowilo Mini — espace de productivité personnel, entièrement local."""

from pathlib import Path
import sqlite3
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

from sowilo_data import Store, StorageError, search_text, summarize_text, extract_text, read_text_file


class SowiloMini(tk.Tk):
    BG = "#14111e"
    PANEL = "#211b30"
    FG = "#f0eafa"
    MUTED = "#b7a9cd"
    PURPLE = "#794ac7"

    def __init__(self, database_path=None):
        super().__init__()
        self.title("ᛋ Sowilo Mini")
        self.geometry("1100x820")
        self.minsize(860, 680)
        self.configure(bg=self.BG)
        self.option_add("*Font", ("Sans", 11))
        self.store = None
        self.note_id = None
        self.note_snapshot = ("", "")
        self.note_revision = None
        self.task_title = tk.StringVar()
        self.file_jobs = queue.Queue()
        self.file_busy = False
        self.file_path = None
        self.file_content = ""
        self.note_rows = []
        self.task_rows = []
        self.page = None
        self.source_editor = None
        self.status = tk.StringVar(value="Prêt · Tout reste sur cet ordinateur")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Control-s>", self.save_shortcut)
        try:
            self.store = Store(database_path or Path(__file__).resolve().with_name("sowilo_mini.sqlite3"))
        except StorageError as error:
            messagebox.showerror("Stockage incompatible", str(error), parent=self)
            self.destroy()
            return
        except (sqlite3.Error, OSError):
            messagebox.showerror("Stockage indisponible", "Impossible d’ouvrir le stockage local. Vérifiez les droits d’accès au dossier puis relancez l’application.", parent=self)
            self.destroy()
            return
        self.build_shell()
        self.navigate("Accueil")

    def label(self, parent, text, size=11, bold=False, muted=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"),
                        fg=self.MUTED if muted else self.FG,
                        font=("Sans", size, "bold" if bold else "normal"), anchor="w")

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg=self.PURPLE if primary else self.PANEL, fg=self.FG,
                         activebackground="#9563e0", activeforeground="white",
                         relief="flat", borderwidth=0, padx=14, pady=10,
                         cursor="hand2", highlightthickness=1,
                         highlightbackground="#3c3052", highlightcolor="#c9a5ff")

    def text_area(self, parent, height=12):
        return ScrolledText(parent, height=height, wrap="word", bg=self.PANEL,
                            fg=self.FG, insertbackground="#c9a5ff",
                            selectbackground=self.PURPLE, selectforeground="white",
                            exportselection=False, relief="flat", padx=14, pady=12,
                            font=("Sans", 12), undo=True, highlightthickness=1,
                            highlightbackground="#3c3052", highlightcolor="#a579ed")

    def entry(self, parent, variable):
        return tk.Entry(parent, textvariable=variable, bg=self.PANEL, fg=self.FG,
                        insertbackground=self.FG, relief="flat", highlightthickness=1,
                        highlightbackground="#3c3052", highlightcolor="#a579ed")

    def listbox(self, parent):
        return tk.Listbox(parent, bg=self.PANEL, fg=self.FG, selectbackground=self.PURPLE,
                          selectforeground="white", exportselection=False,
                          relief="flat", activestyle="none", width=25,
                          highlightthickness=0)

    def build_shell(self):
        sidebar = tk.Frame(self, bg=self.PANEL, width=180, padx=16, pady=24)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.label(sidebar, "ᛋ Sowilo", 21, True).pack(anchor="w")
        self.label(sidebar, "MINI · LOCAL", 9, muted=True).pack(anchor="w", pady=(4, 32))
        self.nav_buttons = {}
        for name in ("Accueil", "Notes", "Tâches", "Fichiers"):
            button = self.button(sidebar, name, lambda page=name: self.navigate(page))
            button.pack(fill="x", pady=5)
            self.nav_buttons[name] = button
        self.label(sidebar, "Votre espace privé\nSans connexion", 10, muted=True).pack(side="bottom", anchor="w")
        main = tk.Frame(self, bg=self.BG, padx=24, pady=20)
        main.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(main, bg=self.BG)
        self.content.pack(fill="both", expand=True)
        self.label(main, "RÉSULTAT DES ACTIONS", 9, True, True).pack(anchor="w", pady=(14, 6))
        self.result = self.text_area(main, 5)
        self.result.pack(fill="x")
        self.result.configure(state="disabled")
        tk.Label(main, textvariable=self.status, bg=self.BG, fg=self.MUTED,
                 font=("Sans", 9), anchor="w").pack(fill="x", pady=10)
        bar = tk.Frame(main, bg=self.BG)
        bar.pack(fill="x")
        for col, (title, command) in enumerate((("Rechercher", self.search),
                                               ("Résumer", self.summarize),
                                               ("Extraire", self.extract))):
            bar.columnconfigure(col, weight=1, uniform="actions")
            self.button(bar, title, command, True).grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0))

    def run_data(self, action):
        try:
            return True, action()
        except StorageError as error:
            messagebox.showwarning("Données à actualiser", str(error), parent=self)
        except ValueError as error:
            messagebox.showwarning("À compléter", str(error), parent=self)
        except (sqlite3.Error, OSError):
            messagebox.showerror("Enregistrement indisponible", "Impossible d’accéder aux données locales. Vérifiez l’espace libre et les droits d’accès, puis réessayez.", parent=self)
        return False, None

    def note_values(self):
        return self.note_title.get(), self.editor.get("1.0", "end-1c")

    def leave_note(self):
        if self.page != "Notes" or self.note_values() == self.note_snapshot:
            return True
        choice = messagebox.askyesnocancel("Note modifiée", "Enregistrer les modifications avant de continuer ?", parent=self)
        if choice is None:
            return False
        return self.save_note() if choice else True

    def navigate(self, page):
        if page == self.page:
            return
        if not self.leave_note():
            return
        for widget in self.content.winfo_children():
            widget.destroy()
        self.page = page
        self.source_editor = None
        for name, button in self.nav_buttons.items():
            button.configure(bg=self.PURPLE if name == page else self.PANEL)
        self.label(self.content, page, 24, True).pack(anchor="w", pady=(0, 6))
        subtitles = {"Accueil": "Une vue claire de votre journée.", "Notes": "Capturez vos idées et retrouvez-les facilement.",
                      "Tâches": "Avancez une tâche à la fois.", "Fichiers": "Consultez vos fichiers texte et Markdown en UTF-8."}
        self.label(self.content, subtitles[page], muted=True).pack(anchor="w", pady=(0, 18))
        self.show_result("Sélectionnez du texte ou utilisez le contenu de cette vue.", "Prêt · " + page)
        {"Accueil": self.build_home, "Notes": self.build_notes,
         "Tâches": self.build_tasks, "Fichiers": self.build_files}[page]()

    def build_home(self):
        ok, stats = self.run_data(self.store.stats)
        if not ok:
            self.status.set("Accueil indisponible · Changez de vue puis réessayez")
            return
        cards = tk.Frame(self.content, bg=self.BG)
        cards.pack(fill="x", pady=(0, 18))
        for col, (title, value) in enumerate((("Notes", stats["notes"]), ("À faire", stats["pending"]), ("Terminées", stats["done"]))):
            cards.columnconfigure(col, weight=1, uniform="stats")
            card = tk.Frame(cards, bg=self.PANEL, padx=18, pady=14)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
            self.label(card, str(value), 26, True).pack(anchor="w")
            self.label(card, title, muted=True).pack(anchor="w")
        self.label(self.content, "APERÇU DE VOTRE ESPACE", 10, True, True).pack(anchor="w", pady=(0, 8))
        self.home_text = self.text_area(self.content, 10)
        self.home_text.pack(fill="both", expand=True)
        ok, data = self.run_data(lambda: (self.store.recent_notes(), self.store.tasks()))
        if ok:
            notes, tasks = data
            preview = "NOTES RÉCENTES\n" + ("\n\n".join(n["title"] + "\n" + n["content"][:240] for n in notes[:3]) or "Aucune note. Créez votre première note dans Notes.")
            preview += "\n\nTÂCHES À FAIRE\n" + ("\n".join("☐ " + t["title"] for t in tasks if not t["done"]) or "Aucune tâche en attente.")
            self.home_text.insert("1.0", preview)
        else:
            self.status.set("Aperçu indisponible · Changez de vue puis réessayez")
        self.home_text.configure(state="disabled")
        self.source_editor = self.home_text

    def build_notes(self):
        tools = tk.Frame(self.content, bg=self.BG)
        tools.pack(fill="x", pady=(0, 10))
        for title, command in (("Nouvelle note", self.new_note), ("Enregistrer", self.save_note), ("Supprimer", self.delete_note), ("Actualiser", self.reload_note)):
            self.button(tools, title, command, title == "Enregistrer").pack(side="left", padx=(0, 8))
        body = tk.Frame(self.content, bg=self.BG)
        body.pack(fill="both", expand=True)
        self.notes_list = self.listbox(body)
        self.notes_list.pack(side="left", fill="y", padx=(0, 14))
        self.notes_list.bind("<<ListboxSelect>>", self.select_note)
        edit = tk.Frame(body, bg=self.BG)
        edit.pack(side="left", fill="both", expand=True)
        self.note_title = tk.StringVar()
        self.label(edit, "Titre", muted=True).pack(anchor="w")
        self.entry(edit, self.note_title).pack(fill="x", ipady=8, pady=(4, 10))
        self.editor = self.text_area(edit)
        self.editor.pack(fill="both", expand=True)
        self.source_editor = self.editor
        self.restore_active_note()
        self.button(self.content, "Enregistrer une copie", lambda: self.save_note(as_copy=True)).pack(anchor="w", pady=(8, 0))

    def restore_active_note(self):
        active_id = self.note_id
        self.load_note(None)
        if active_id is not None:
            ok, note = self.run_data(lambda: self.store.get_note(active_id))
            if ok:
                self.load_note(note)
        self.refresh_notes()

    def refresh_notes(self):
        ok, notes = self.run_data(self.store.note_headers)
        if not ok:
            self.sync_note_selection()
            self.status.set("Liste des notes indisponible · Réessayez avec Actualiser")
            return False
        self.note_rows = notes
        self.notes_list.delete(0, "end")
        for index, note in enumerate(notes):
            self.notes_list.insert("end", note["title"])
        self.sync_note_selection()
        return True

    def sync_note_selection(self):
        self.notes_list.selection_clear(0, "end")
        for index, note in enumerate(self.note_rows):
            if note["id"] == self.note_id:
                self.notes_list.selection_set(index)
                self.notes_list.see(index)

    def load_note(self, note):
        self.note_id = note["id"] if note else None
        self.note_revision = note["revision"] if note else None
        self.note_title.set(note["title"] if note else "")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", note["content"] if note else "")
        self.editor.edit_reset()
        self.note_snapshot = self.note_values()

    def select_note(self, event=None):
        selection = self.notes_list.curselection()
        if not selection:
            return
        note = self.note_rows[selection[0]]
        if note["id"] == self.note_id:
            return
        if self.leave_note():
            ok, current = self.run_data(lambda: self.store.get_note(note["id"]))
            if ok:
                self.load_note(current)
        self.refresh_notes()

    def reload_note(self):
        if not self.leave_note():
            return
        if self.note_id is not None:
            ok, note = self.run_data(lambda: self.store.get_note(self.note_id))
            if not ok:
                return
            self.load_note(note)
        else:
            self.load_note(None)
        if self.refresh_notes():
            self.status.set("Notes actualisées")

    def refreshed_status(self, success, message):
        self.status.set(message if success else message + " · Liste non actualisée, réessayez avec Actualiser")

    def new_note(self):
        if self.leave_note():
            self.load_note(None)
            self.notes_list.selection_clear(0, "end")
            self.status.set("Nouvelle note · Enregistrez pour la conserver")

    def save_note(self, as_copy=False):
        title, content = self.note_values()
        target_id = None if as_copy else self.note_id
        ok, note_id = self.run_data(lambda: self.store.save_note(
            title, content, target_id, self.note_revision if target_id is not None else None))
        if ok:
            self.note_id = note_id
            self.note_revision = self.note_revision + 1 if target_id is not None else 1
            self.note_title.set(title.strip())
            self.note_snapshot = self.note_values()
            self.refreshed_status(self.refresh_notes(), "Note enregistrée localement")
        return ok

    def save_shortcut(self, event=None):
        if self.page == "Notes":
            self.save_note()
        return "break"

    def delete_note(self):
        if self.note_id is None:
            self.status.set("Sélectionnez une note enregistrée à supprimer")
            return
        if messagebox.askyesno("Supprimer la note", "Supprimer définitivement cette note et ses modifications ?", parent=self):
            ok, _ = self.run_data(lambda: self.store.delete_note(self.note_id, self.note_revision))
            if ok:
                self.load_note(None)
                self.refreshed_status(self.refresh_notes(), "Note supprimée")

    def build_tasks(self):
        tools = tk.Frame(self.content, bg=self.BG)
        tools.pack(fill="x", pady=(0, 12))
        field = self.entry(tools, self.task_title)
        field.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 8))
        field.bind("<Return>", lambda event: self.add_task())
        self.button(tools, "Ajouter", self.add_task, True).pack(side="left")
        self.tasks_list = self.listbox(self.content)
        self.tasks_list.pack(fill="both", expand=True)
        self.tasks_list.bind("<Double-Button-1>", self.task_toggle_event)
        self.tasks_list.bind("<space>", self.task_toggle_event)
        actions = tk.Frame(self.content, bg=self.BG)
        actions.pack(fill="x", pady=(10, 0))
        self.button(actions, "Terminer / Réactiver", self.toggle_task).pack(side="left", padx=(0, 8))
        self.button(actions, "Supprimer", self.delete_task).pack(side="left", padx=(0, 8))
        self.button(actions, "Actualiser", self.refresh_tasks).pack(side="left")
        self.refresh_tasks()

    def task_toggle_event(self, event=None):
        self.toggle_task()
        return "break"

    def refresh_tasks(self):
        selection = self.tasks_list.curselection()
        selected_id = self.task_rows[selection[0]]["id"] if selection else None
        ok, tasks = self.run_data(self.store.tasks)
        if ok:
            self.task_rows = tasks
            self.tasks_list.delete(0, "end")
            for index, task in enumerate(tasks):
                self.tasks_list.insert("end", ("✓  " if task["done"] else "☐  ") + task["title"])
                if task["done"]:
                    self.tasks_list.itemconfig("end", fg=self.MUTED)
                if task["id"] == selected_id:
                    self.tasks_list.selection_set(index)
                    self.tasks_list.see(index)
            self.status.set("Tâches actualisées")
            return True
        self.status.set("Liste des tâches indisponible · Réessayez avec Actualiser")
        return False

    def add_task(self):
        ok, _ = self.run_data(lambda: self.store.add_task(self.task_title.get()))
        if ok:
            self.task_title.set("")
            self.refreshed_status(self.refresh_tasks(), "Tâche créée")

    def selected_task(self):
        selection = self.tasks_list.curselection()
        if not selection:
            self.status.set("Sélectionnez une tâche dans la liste")
            return None
        return self.task_rows[selection[0]]

    def toggle_task(self):
        task = self.selected_task()
        if task is not None:
            ok, _ = self.run_data(lambda: self.store.set_task_done(task["id"], not task["done"], expected_done=task["done"]))
            if ok:
                self.refreshed_status(self.refresh_tasks(), "État de la tâche mis à jour")

    def delete_task(self):
        task = self.selected_task()
        if task is not None and messagebox.askyesno("Supprimer la tâche", "Supprimer définitivement cette tâche ?", parent=self):
            ok, _ = self.run_data(lambda: self.store.delete_task(task["id"]))
            if ok:
                self.refreshed_status(self.refresh_tasks(), "Tâche supprimée")

    def build_files(self):
        tools = tk.Frame(self.content, bg=self.BG)
        tools.pack(fill="x", pady=(0, 12))
        self.button(tools, "Ouvrir un fichier…", self.open_file, True).pack(side="left")
        self.file_label = self.label(tools, self.file_path.name if self.file_path else "Aucun fichier ouvert", muted=True)
        self.file_label.pack(side="left", padx=12)
        self.file_editor = self.text_area(self.content)
        self.file_editor.pack(fill="both", expand=True)
        self.file_editor.insert("1.0", self.file_content)
        self.file_editor.configure(state="disabled")
        self.source_editor = self.file_editor
        self.label(self.content, "Lecture seule · .txt / .md · UTF-8 · 2 Mo maximum", 9, muted=True).pack(anchor="w", pady=(8, 0))

    def open_file(self):
        if self.file_busy:
            self.status.set("Une lecture de fichier est déjà en cours")
            return
        filename = filedialog.askopenfilename(parent=self, title="Ouvrir un fichier texte",
                                              filetypes=(("Texte et Markdown", "*.txt *.md"), ("Texte", "*.txt"), ("Markdown", "*.md")))
        if not filename:
            return
        self.file_busy = True
        self.status.set("Lecture du fichier en cours…")
        threading.Thread(target=self.read_file_job, args=(filename, self.file_jobs), daemon=True).start()
        self.after(50, self.poll_file_job)

    @staticmethod
    def read_file_job(filename, results):
        # Aucun accès à Tkinter depuis le fil de lecture.
        try:
            results.put((filename, read_text_file(filename), None))
        except ValueError as error:
            results.put((filename, None, str(error)))
        except Exception:
            results.put((filename, None, "Impossible de lire ce fichier. Vérifiez qu’il existe et que vous avez le droit de l’ouvrir."))

    def poll_file_job(self):
        try:
            filename, content, error = self.file_jobs.get_nowait()
        except queue.Empty:
            self.after(50, self.poll_file_job)
            return
        self.file_busy = False
        if error:
            messagebox.showerror("Lecture impossible", error, parent=self)
            self.status.set("Fichier non ouvert · Réessayez ou choisissez un autre fichier")
            return
        self.file_path = Path(filename)
        self.file_content = content
        if self.page == "Fichiers":
            self.file_label.configure(text=self.file_path.name)
            self.file_editor.configure(state="normal")
            self.file_editor.delete("1.0", "end")
            self.file_editor.insert("1.0", content)
            self.file_editor.configure(state="disabled")
        self.status.set("Fichier ouvert · " + self.file_path.name)

    def get_text(self):
        if self.source_editor is not None:
            try:
                return self.source_editor.get("sel.first", "sel.last")
            except tk.TclError:
                return self.source_editor.get("1.0", "end-1c")
        if self.page == "Tâches":
            selection = self.tasks_list.curselection()
            tasks = [self.task_rows[selection[0]]] if selection else self.task_rows
            return "\n".join(("Terminée : " if t["done"] else "À faire : ") + t["title"] for t in tasks)
        return ""

    def show_result(self, text, status):
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", text)
        self.result.configure(state="disabled")
        self.status.set(status)

    def action_text(self):
        text = self.get_text()
        if not text.strip():
            self.show_result("Ajoutez une note, une tâche ou ouvrez un fichier texte pour utiliser cette action.", "Aucun contenu à traiter")
            return None
        return text

    def search(self):
        text = self.action_text()
        if text is None:
            return
        query = simpledialog.askstring("Rechercher", "Mot ou expression à rechercher :", parent=self)
        if query is None:
            return
        try:
            result = search_text(text, query)
        except ValueError as error:
            self.show_result(str(error), "Recherche vide")
            return
        self.show_result(result, "Recherche locale · Mots entiers, sans distinction de casse")

    def summarize(self):
        text = self.action_text()
        if text is not None:
            self.show_result(summarize_text(text), "Résumé local · Trois premières phrases au maximum")

    def extract(self):
        text = self.action_text()
        if text is not None:
            self.show_result(extract_text(text), "Extraction locale · Liens, e-mails, dates et listes")

    def close(self):
        if not self.leave_note():
            return
        if self.store is not None:
            self.store.close()
        self.destroy()


if __name__ == "__main__":
    SowiloMini().mainloop()
