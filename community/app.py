"""Community shell: local productivity, optional AI and restartable first-run guide."""
from pathlib import Path
import queue
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from sowilo_mini import SowiloMini
from sowilo_data import search_text
from modules.documents import DocumentsService, DocumentError
from .ai import SYSTEM, MAX_INPUT, analyze, create_client, prepare_chat
from .config import ConfigurationError
from .data_tools import save_backup, read_backup, restore_backup, export_notes
from .dialogs import NoteReview
from .groq import GroqError
from .theme import NeonTheme, NEON, BORDER, SURFACE, FONT, rune, WelcomeBanner, RoundedPanel

APP_ROOT = Path(__file__).resolve().parent.parent

GUIDE = (
    ("Bienvenue dans Community", "Votre espace gratuit pour les notes, les tâches, les documents et le chat.\n\nNotes, tâches et lecture fonctionnent sans compte ni connexion. L’IA est facultative.\n\nSowilo prépare et explique ; vous gardez la décision.", "Découvrir l’accueil", "Accueil"),
    ("Connecter votre IA", "Dans Configuration, saisissez votre clé Groq et testez la connexion.\n\nLa clé reste en mémoire, ou dans le coffre sécurisé si vous le demandez. Le fournisseur peut facturer ses API.\n\nVous pouvez passer cette étape et revenir plus tard.", "Configurer Groq", "Configuration"),
    ("Votre premier espace", "Créez une note et une tâche, puis ouvrez un document d’exemple.\n\nVos données sont enregistrées dans l’espace privé de Community. Aucun autre projet Sowilo n’est importé.", "Essayer les notes", "Notes"),
    ("Les trois actions rapides", "Sur un texte sélectionné ou le contenu de la vue : Résumer, Rechercher, Extraire.\n\nChaque action IA demande votre accord avant l’envoi du texte à Groq. La recherche locale fonctionne sans IA.\n\nRetrouvez ce guide dans Aide / Premiers pas.", "Ouvrir un exemple", "Exemple"),
)


class CommunityApp(NeonTheme, SowiloMini):
    def __init__(self, config):
        self.settings = config
        self.jobs = queue.Queue()
        self.busy = False
        self.job_kind = None
        self.last_result = ""
        self.chat_messages = []
        self.chat_draft = ""
        self.last_chat_output = ""
        self.chat_consent = False
        super().__init__(config.paths.data_dir / "community.sqlite3")
        if not self.winfo_exists():
            return
        self.title("ᛋ Sowilo Community · V1")
        self.minsize(900, 680)
        width = min(1180, max(900, self.winfo_screenwidth() - 80))
        height = min(850, max(680, self.winfo_screenheight() - 80))
        self.geometry(f"{width}x{height}")
        self.status.set("Prêt · Notes, tâches et lecture locales · IA facultative")
        if not config.guide_completed and not config.guide_dismissed:
            self.after(200, lambda: self.navigate("Aide"))

    def build_shell(self):
        sidebar = tk.Frame(self, bg=self.PANEL, width=210, padx=16, pady=16)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        rune(sidebar, 64).pack(anchor="w", pady=(0, 2))
        self.label(sidebar, "S O W I L O", 17, True).pack(anchor="w")
        self.label(sidebar, "C O M M U N I T Y   /   V 1", 8, muted=True).pack(anchor="w", pady=(5, 14))
        tk.Frame(sidebar, bg=NEON, height=1).pack(fill="x", pady=(0, 18))
        self.label(sidebar, "VOTRE ESPACE", 8, True, True).pack(anchor="w", pady=(0, 8))
        self.nav_buttons = {}
        for name in ("Accueil", "Notes", "Tâches", "Documents", "Chat", "Configuration", "Aide"):
            button = self.button(sidebar, name, lambda page=name: self.navigate(page))
            button.configure(anchor="w", padx=17)
            button.pack(fill="x", pady=2)
            self.nav_buttons[name] = button
        footer = tk.Frame(sidebar, bg=self.PANEL)
        footer.pack(side="bottom", fill="x", pady=(12, 0))
        tk.Frame(footer, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))
        self.label(footer, "ᛋ  VOTRE OUTIL. VOS BRIQUES.", 8, True).pack(anchor="w")
        self.label(footer, "Données locales · IA facultative", 8, muted=True).pack(anchor="w", pady=(5, 0))
        tk.Frame(self, bg=BORDER, width=1).pack(side="left", fill="y")
        main = tk.Frame(self, bg=self.BG, padx=22, pady=16)
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=self.BG)
        top.pack(fill="x", pady=(0, 12))
        self.label(top, "SOWILO  /  COMMUNITY", 9, True, True).pack(side="left")
        self.result_toggle = self.button(top, "Dernier résultat", lambda: self.show_result(self.last_result, "Dernier résultat disponible"))
        self.result_toggle.configure(state="disabled", pady=5)
        self.result_toggle.pack(side="right")
        tk.Frame(main, bg=BORDER, height=1).pack(fill="x", pady=(0, 18))
        self.content = tk.Frame(main, bg=self.BG)
        self.content.pack(fill="both", expand=True)
        self.result_container = tk.Frame(main, bg=self.BG)
        tools = tk.Frame(self.result_container, bg=self.BG)
        tools.pack(fill="x", pady=(8, 5))
        self.label(tools, "RÉSULTAT · À RELIRE", 8, True, True).pack(side="left")
        for label, command in (("Copier", lambda: self.copy_response(from_result=True)),
                               ("Note", lambda: self.response_to_note(from_result=True)),
                               ("Tâche", lambda: self.response_to_task(from_result=True)), ("Replier", self.hide_result)):
            self.button(tools, label, command).pack(side="left", padx=(7, 0))
        self.result = self.text_area(self.result_container, 3)
        self.result.pack(fill="x")
        self.result.configure(state="disabled")
        self.status_widget = tk.Label(main, textvariable=self.status, bg=self.BG, fg=self.MUTED,
                 font=(FONT, 9), anchor="w", wraplength=850)
        self.status_widget.pack(fill="x", pady=8)
        self.action_bar = tk.Frame(main, bg=self.BG)
        self.action_bar.pack(fill="x")
        self.action_buttons = {}
        for i, (label, command) in enumerate((("Résumer", self.summarize), ("Rechercher", self.search), ("Extraire", self.extract))):
            self.action_bar.columnconfigure(i, weight=1, uniform="actions")
            button = self.button(self.action_bar, label, command, True)
            button.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            self.action_buttons[label] = button
        self.bind("<KeyRelease>", lambda event: self.refresh_actions(), add="+")
        self.bind("<ButtonRelease-1>", lambda event: self.refresh_actions(), add="+")

    def show_result(self, text, status):
        self.last_result = text
        self.result_toggle.configure(state="normal")
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", text)
        self.result.configure(state="disabled")
        self.result_container.pack(fill="x", before=self.status_widget)
        self.status.set(status)

    def hide_result(self):
        self.result_container.pack_forget()

    def refresh_actions(self):
        if not hasattr(self, "action_buttons"):
            return
        relevant = self.page in ("Accueil", "Notes", "Tâches", "Documents")
        if relevant:
            self.action_bar.pack(fill="x")
        else:
            self.action_bar.pack_forget()
        has_text = False
        if relevant and self.source_editor is not None:
            try:
                has_text = bool(self.source_editor.get("1.0", "1.0 + 128 chars").strip()) or self.source_editor.compare("end-1c", ">", "1.0 + 128 chars")
            except tk.TclError:
                pass
        elif self.page == "Tâches":
            has_text = bool(self.task_rows)
        connected = self.settings.has_api_key()
        for label, button in self.action_buttons.items():
            enabled = relevant and has_text and not self.busy and (label == "Rechercher" or connected)
            button.configure(state="normal" if enabled else "disabled")

    def source_context(self):
        scope = "Document entier" if self.page == "Documents" else "Contenu de la vue"
        if self.source_editor is not None:
            try:
                if self.source_editor.get("sel.first", "sel.last"):
                    scope = "Sélection"
            except tk.TclError:
                pass
        if self.page == "Tâches":
            scope = "Tâche sélectionnée" if self.tasks_list.curselection() else "Toutes les tâches"
        elif self.page == "Notes" and scope != "Sélection":
            scope = "Note entière"
        source = self.file_path.name if self.page == "Documents" and self.file_path else self.page
        return scope + " · " + source

    def reusable_text(self, from_result=False):
        chat = self.page == "Chat" and not from_result
        widget = self.chat_output if chat else self.result
        try:
            selected = widget.get("sel.first", "sel.last")
            if selected.strip():
                return selected
        except tk.TclError:
            pass
        return self.last_chat_output if chat else self.last_result

    def copy_response(self, *, from_result=False):
        text = self.reusable_text(from_result=True) if from_result else self.reusable_text()
        if not text.strip():
            self.status.set("Aucun résultat à copier")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.set("Texte copié · Le presse-papiers est partagé avec les autres applications")

    def response_to_note(self, *, from_result=False):
        text = self.reusable_text(from_result=True) if from_result else self.reusable_text()
        if not text.strip():
            return
        review = NoteReview(self, text)
        if review.result:
            ok, _ = self.run_data(lambda: self.store.save_note(*review.result))
            if ok:
                self.status.set("Nouvelle note enregistrée après relecture")
                if self.page == "Notes":
                    self.refresh_notes()

    def response_to_task(self, *, from_result=False):
        text = self.reusable_text(from_result=True) if from_result else self.reusable_text()
        if not text.strip():
            return
        title = simpledialog.askstring("Relire la tâche", "Modifiez et confirmez la tâche à créer (300 caractères maximum) :",
                                       initialvalue=text.strip()[:300], parent=self)
        if title is not None:
            ok, _ = self.run_data(lambda: self.store.add_task(title))
            if ok:
                self.status.set("Tâche créée après confirmation")
                if self.page == "Tâches":
                    self.refresh_tasks()

    def paragraph(self, text, parent=None):
        parent = parent or self.content
        widget = tk.Label(parent, text=text, justify="left", anchor="nw", wraplength=760,
                          bg=parent.cget("bg"), fg=self.MUTED, font=(FONT, 11))
        widget.pack(fill="x", pady=(0, 12))
        return widget

    def scroll_form(self):
        host = tk.Frame(self.content, bg=self.BG)
        host.pack(fill="both", expand=True)
        canvas = tk.Canvas(host, bg=self.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(host, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        form = tk.Frame(canvas, bg=self.BG)
        window = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
        return form

    def navigate(self, page, force=False):
        if self.busy and self.job_kind == "configuration":
            self.status.set("Vérification de configuration en cours · Patientez")
            return
        if page == self.page and not force:
            return
        if not self.leave_note():
            return
        if self.page == "Chat" and hasattr(self, "chat_input"):
            self.chat_draft = self.chat_input.get("1.0", "end-1c")
        for widget in self.content.winfo_children():
            widget.destroy()
        self.page = page
        self.source_editor = None
        for name, button in self.nav_buttons.items():
            button.configure(bg=self.PURPLE if name == page else SURFACE,
                             highlightbackground=NEON if name == page else BORDER)
        self.label(self.content, "Premiers pas & aide" if page == "Aide" else page, 24, True).pack(anchor="w", pady=(0, 12))
        self.hide_result()
        self.status.set("Traitement en cours · Vous pouvez continuer à travailler" if self.busy else "Prêt · " + page)
        {"Accueil": self.build_home, "Notes": self.build_notes, "Tâches": self.build_tasks,
         "Documents": self.build_documents, "Chat": self.build_chat,
         "Configuration": self.build_settings, "Aide": self.build_guide}[page]()
        self.refresh_actions()

    def build_home(self):
        WelcomeBanner(self.content).pack(fill="x", pady=(0, 16))
        ok, stats = self.run_data(self.store.stats)
        if not ok:
            return
        cards = tk.Frame(self.content, bg=self.BG)
        cards.pack(fill="x", pady=(0, 16))
        for col, (title, value, target) in enumerate((("NOTES", stats["notes"], "Notes"),
                ("À FAIRE", stats["pending"], "Tâches"), ("TERMINÉES", stats["done"], "Tâches"))):
            cards.columnconfigure(col, weight=1, uniform="stats")
            card = tk.Frame(cards, bg=self.PANEL, padx=16, pady=10,
                            highlightthickness=1, highlightbackground=BORDER)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
            self.label(card, title, 8, True, True).pack(anchor="w")
            number = self.label(card, f"{value:02d}", 25, True)
            number.configure(fg=NEON)
            number.pack(anchor="w")
            tk.Frame(card, bg=self.PURPLE, height=2).pack(fill="x", pady=(6, 0))
            card.bind("<Button-1>", lambda event, page=target: self.navigate(page))
        tools = tk.Frame(self.content, bg=self.BG)
        tools.pack(fill="x", pady=(0, 12))
        for index, (label, target) in enumerate((("Mes idées  →", "Notes"),
                ("Mes documents  →", "Documents"), ("Parler à Sowilo  →", "Chat"))):
            tools.columnconfigure(index, weight=1, uniform="shortcuts")
            self.button(tools, label, lambda page=target: self.navigate(page),
                        primary=target == "Chat").grid(row=0, column=index, sticky="ew",
                        padx=(0 if index == 0 else 8, 0))
        self.label(self.content, "VOTRE ACTIVITÉ RÉCENTE", 8, True, True).pack(anchor="w", pady=(0, 6))
        self.home_text = self.text_area(self.content, 6)
        self.home_text.pack(fill="both", expand=True)
        ok, data = self.run_data(lambda: (self.store.recent_notes(), self.store.tasks()))
        if ok:
            notes, tasks = data
            preview = "NOTES RÉCENTES\n" + ("\n\n".join(n["title"] + "\n" + n["content"][:240] for n in notes[:3]) or "Votre première idée mérite sa place ici. Créez une note pour commencer.")
            preview += "\n\nTÂCHES À FAIRE\n" + ("\n".join("☐ " + t["title"] for t in tasks if not t["done"]) or "L’esprit libre : aucune tâche en attente.")
            self.home_text.insert("1.0", preview)
        else:
            self.status.set("Aperçu indisponible · Changez de vue puis réessayez")
        self.home_text.configure(state="disabled")
        self.source_editor = self.home_text

    def panel(self, parent, **options):
        panel = RoundedPanel(parent, **options)
        return panel, panel.body

    def build_notes(self):
        body = tk.Frame(self.content, bg=self.BG)
        body.pack(fill="both", expand=True)
        collection, left = self.panel(body, width=195)
        collection.pack(side="left", fill="y", padx=(0, 12))
        self.label(left, "VOTRE CARNET", 8, True, True).pack(anchor="w", pady=(0, 10))
        self.button(left, "+ Nouvelle note", self.new_note, True).pack(fill="x", pady=(0, 8))
        self.notes_list = self.listbox(left)
        self.notes_list.configure(width=16, borderwidth=0, highlightthickness=0,
                                  selectborderwidth=0)
        self.notes_list.pack(fill="both", expand=True, pady=(4, 8))
        self.notes_list.bind("<<ListboxSelect>>", self.select_note)
        self.button(left, "Actualiser", self.reload_note).pack(fill="x")
        paper, edit = self.panel(body)
        paper.pack(side="left", fill="both", expand=True)
        self.label(edit, "UNE IDÉE À GARDER", 8, True, True).pack(anchor="w", pady=(0, 8))
        self.note_title = tk.StringVar()
        self.label(edit, "Titre de la note", 10, muted=True).pack(anchor="w")
        self.entry(edit, self.note_title).pack(fill="x", ipady=8, pady=(5, 10))
        self.editor = self.text_area(edit)
        self.editor.configure(highlightbackground=self.PANEL, font=(FONT, 12), padx=5)
        self.editor.pack(fill="both", expand=True)
        self.source_editor = self.editor
        bar = tk.Frame(edit, bg=self.PANEL)
        bar.pack(fill="x", pady=(10, 0))
        for index, (title, command) in enumerate((("Enregistrer", self.save_note),
                ("Copie", lambda: self.save_note(as_copy=True)), ("Supprimer", self.delete_note))):
            self.button(bar, title, command, index == 0).pack(side="left", padx=(0, 6))
        self.restore_active_note()

    def build_tasks(self):
        capture, field_panel = self.panel(self.content, height=105)
        capture.pack(fill="x", pady=(0, 12))
        self.label(field_panel, "UNE CHOSE À LA FOIS", 8, True, True).pack(anchor="w", pady=(0, 8))
        tools = tk.Frame(field_panel, bg=self.PANEL)
        tools.pack(fill="x")
        field = self.entry(tools, self.task_title)
        field.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        field.bind("<Return>", lambda event: self.add_task())
        self.button(tools, "+ Ajouter", self.add_task, True).pack(side="left")
        board, inside = self.panel(self.content)
        board.pack(fill="both", expand=True)
        self.label(inside, "VOTRE FEUILLE DE ROUTE", 8, True, True).pack(anchor="w", pady=(0, 10))
        self.tasks_list = self.listbox(inside)
        self.tasks_list.configure(highlightthickness=0, font=(FONT, 13),
                                  selectborderwidth=5, relief="flat")
        self.tasks_list.pack(fill="both", expand=True)
        self.tasks_list.bind("<Double-Button-1>", self.task_toggle_event)
        self.tasks_list.bind("<space>", self.task_toggle_event)
        actions = tk.Frame(inside, bg=self.PANEL)
        actions.pack(fill="x", pady=(10, 0))
        for title, command in (("Terminer / Réactiver", self.toggle_task),
                               ("Supprimer", self.delete_task), ("Actualiser", self.refresh_tasks)):
            self.button(actions, title, command).pack(side="left", padx=(0, 8))
        self.refresh_tasks()

    def run_job(self, task, done, status, *, kind="action"):
        if self.busy:
            self.status.set("Une opération est déjà en cours")
            return False
        self.busy = True
        self.job_kind = kind
        self.refresh_actions()
        self.status.set(status)
        results = self.jobs
        def worker():
            try:
                results.put((True, task(), done))
            except (DocumentError, ConfigurationError, GroqError, ValueError) as error:
                results.put((False, str(error), done))
            except Exception:
                results.put((False, "Opération impossible. Vérifiez les fichiers, dépendances ou votre connexion.", done))
        threading.Thread(target=worker, daemon=True).start()
        self.after(60, self.poll_job)
        return True

    def poll_job(self):
        try:
            success, result, done = self.jobs.get_nowait()
        except queue.Empty:
            self.after(60, self.poll_job)
            return
        self.busy = False
        kind = self.job_kind
        self.job_kind = None
        if success:
            done(result)
        else:
            self.show_result(result, "Opération interrompue · Vos données locales sont conservées")
        if kind == "chat" and self.page == "Chat":
            self.chat_input.configure(state="normal")
        self.refresh_actions()

    def build_documents(self):
        self.paragraph("Lecture locale · TXT, Markdown, PDF textuels, DOCX · Sans OCR · Sources jusqu’à 20 Mio")
        tools = tk.Frame(self.content, bg=self.BG)
        tools.pack(fill="x", pady=(0, 10))
        self.button(tools, "Ouvrir un document…", self.open_document, True).pack(side="left")
        self.button(tools, "Essayer un exemple", self.open_example).pack(side="left", padx=8)
        self.file_label = self.label(self.content, self.file_path.name if self.file_path else "Aucun document ouvert", muted=True)
        self.file_label.pack(anchor="w", pady=(0, 6))
        self.file_editor = self.text_area(self.content)
        self.file_editor.pack(fill="both", expand=True)
        self.file_editor.insert("1.0", self.file_content)
        self.file_editor.configure(state="disabled")
        self.source_editor = self.file_editor

    def open_document(self):
        if self.busy:
            return
        filename = filedialog.askopenfilename(parent=self, title="Ouvrir un document",
            filetypes=(("Documents", "*.txt *.md *.pdf *.docx"),))
        if filename:
            self.load_document(Path(filename))

    def open_example(self):
        self.navigate("Documents")
        if self.page == "Documents":
            self.load_document(APP_ROOT / "examples" / "bienvenue.txt", example=True)

    def load_document(self, path, example=False):
        if self.busy:
            return
        try:
            path = path.resolve(strict=True)
            # Only bundled examples bypass user directory authorization.
            if example and path.parent != (APP_ROOT / "examples").resolve():
                raise ConfigurationError("Exemple inconnu.")
            if not example and not any(path.is_relative_to(root) for root in self.settings.roots):
                if not messagebox.askyesno("Autoriser ce dossier", f"Autoriser la lecture dans ce dossier et ses sous-dossiers ?\n\n{path.parent}\n\nAucun fichier ne sera envoyé automatiquement. Vous pourrez retirer l’autorisation dans Configuration.", parent=self):
                    return
                self.settings.authorize_root(path.parent)
            service = DocumentsService([path.parent] if example else self.settings.roots)
        except (ConfigurationError, DocumentError, OSError):
            self.show_result("Document inaccessible ou dossier non autorisé.", "Lecture impossible")
            return
        def done(text):
            self.file_path, self.file_content = path, text
            if self.page == "Documents":
                self.file_label.configure(text=path.name)
                self.file_editor.configure(state="normal")
                self.file_editor.delete("1.0", "end")
                self.file_editor.insert("1.0", text)
                self.file_editor.configure(state="disabled")
            self.status.set("Document lu localement · " + path.name)
            self.refresh_actions()
        self.run_job(lambda: service.read(path), done, "Lecture locale du document…")

    def build_chat(self):
        conversation, body = self.panel(self.content)
        conversation.pack(fill="both", expand=True, pady=(0, 10))
        heading = tk.Frame(body, bg=self.PANEL)
        heading.pack(fill="x", pady=(0, 8))
        self.label(heading, "ᛋ  SOWILO", 13, True).pack(side="left")
        self.label(heading, "HISTORIQUE NON ENREGISTRÉ", 8, muted=True).pack(side="right")
        self.chat_output = self.text_area(body, 7)
        self.chat_output.configure(highlightthickness=0, padx=8, spacing3=10)
        self.chat_output.pack(fill="both", expand=True)
        self.render_chat()
        composer, inside = self.panel(self.content, height=145, padding=12)
        composer.pack(fill="x")
        self.chat_input = self.text_area(inside, 2)
        self.chat_input.configure(highlightthickness=0, padx=6, pady=5)
        self.chat_input.pack(fill="both", expand=True)
        self.chat_input.insert("1.0", self.chat_draft)
        self.chat_input.bind("<Control-Return>", self.send_chat)
        if self.busy and self.job_kind == "chat":
            self.chat_input.configure(state="disabled")
        reuse = tk.Frame(body, bg=self.PANEL)
        reuse.pack(fill="x", pady=(6, 0))
        for title, command in (("Copier", self.copy_response), ("Créer une note", self.response_to_note), ("Créer une tâche", self.response_to_task)):
            self.button(reuse, title, command).pack(side="left", padx=(0, 6))
        bar = tk.Frame(inside, bg=self.PANEL)
        bar.pack(fill="x", pady=(5, 0))
        self.button(bar, "Envoyer  →", self.send_chat, True).pack(side="right")
        self.button(bar, "Nouvelle conversation", self.reset_chat).pack(side="left")
        self.label(bar, "Ctrl + Entrée", 8, muted=True).pack(side="left", padx=10)

    def render_chat(self):
        self.chat_output.configure(state="normal")
        self.chat_output.delete("1.0", "end")
        self.chat_output.tag_configure("speaker", foreground=NEON, font=(FONT, 9, "bold"),
                                       spacing1=12, spacing3=5)
        self.chat_output.tag_configure("assistant", foreground=self.FG, lmargin1=12,
                                       lmargin2=12, rmargin=28, spacing3=12)
        self.chat_output.tag_configure("user", foreground="#e6d1ff", background="#231632",
                                       lmargin1=25, lmargin2=25, rmargin=12, spacing1=8, spacing3=12)
        self.chat_output.tag_configure("welcome", foreground=self.FG, font=(FONT, 19, "bold"), spacing1=14, spacing3=12)
        self.chat_output.tag_configure("hint", foreground=self.MUTED, spacing3=10)
        for item in self.chat_messages:
            user = item["role"] == "user"
            self.chat_output.insert("end", ("VOUS" if user else "ᛋ  SOWILO") + "\n", "speaker")
            self.chat_output.insert("end", item["content"] + "\n\n", "user" if user else "assistant")
        if not self.chat_messages:
            self.chat_output.insert("end", "Qu’avez-vous en tête ?\n", "welcome")
            self.chat_output.insert("end", "Une idée à clarifier, un texte à reformuler, un brouillon à préparer.\n\n", "hint")
            self.chat_output.insert("end", "Seuls vos messages sont envoyés à Groq, après votre accord.\nAucun accès automatique à vos notes ou documents. Les réponses sont à vérifier.", "hint")
        self.chat_output.configure(state="disabled")
        self.chat_output.see("end")

    def client(self):
        key = self.settings.get_api_key()
        if not key:
            raise GroqError("Connectez Groq dans Configuration. Les fonctions locales restent disponibles.")
        return create_client(key, self.settings.model)

    def send_chat(self, event=None):
        if self.busy:
            return "break"
        try:
            text = self.chat_input.get("1.0", "end-1c")
            pending = prepare_chat(self.chat_messages, text)
            client = self.client()
        except (GroqError, ValueError) as error:
            self.show_result(str(error), "Message non envoyé")
            return "break"
        if not self.chat_consent:
            if not messagebox.askyesno("Conversation avec Groq", "Envoyer les messages de cette conversation à Groq ? Les échanges suivants incluront son historique. Des frais ou quotas du fournisseur peuvent s’appliquer.\n\nLes autres données de Community ne seront pas jointes.", parent=self):
                return "break"
            self.chat_consent = True
        self.chat_draft = text
        self.chat_input.configure(state="disabled")
        def done(reply):
            self.chat_messages = pending + [{"role": "assistant", "content": reply}]
            self.last_chat_output = reply
            self.chat_draft = ""
            if self.page == "Chat":
                self.chat_input.configure(state="normal")
                self.chat_input.delete("1.0", "end")
                self.render_chat()
            self.status.set("Réponse Groq disponible dans Chat · À vérifier")
        # Error completion must also restore the draft editor.
        self.run_job(lambda: client.complete([{"role": "system", "content": SYSTEM}] + pending), done, "Groq prépare sa réponse…", kind="chat")
        self.after(100, self.restore_chat_input)
        return "break"

    def restore_chat_input(self):
        if self.busy:
            self.after(100, self.restore_chat_input)
        elif self.page == "Chat":
            self.chat_input.configure(state="normal")

    def reset_chat(self):
        if self.busy:
            return
        if (self.chat_messages or self.chat_input.get("1.0", "end-1c").strip()) and not messagebox.askyesno("Nouvelle conversation", "Effacer la conversation et le brouillon en mémoire ?", parent=self):
            return
        self.chat_messages = []
        self.chat_draft = ""
        self.last_chat_output = ""
        self.chat_consent = False
        self.chat_input.delete("1.0", "end")
        self.render_chat()

    def build_settings(self):
        form = self.scroll_form()
        self.label(form, "VOS DONNÉES", 12, True).pack(anchor="w", pady=(0, 8))
        tools = tk.Frame(form, bg=self.BG)
        tools.pack(fill="x", pady=(0, 10))
        for title, command in (("Sauvegarder", self.backup_data), ("Restaurer", self.restore_data), ("Exporter les notes", self.export_data)):
            self.button(tools, title, command).pack(side="left", padx=(0, 8))
        self.paragraph("Sauvegarde : notes et tâches uniquement, sans clé, conversation ni document externe. Les fichiers exportés ne sont pas chiffrés.", parent=form)
        self.paragraph("Fournisseur disponible : Groq. Les autres connecteurs pourront être ajoutés ensuite. Aucune clé n’est écrite dans un fichier JSON. La clé appartient à votre compte fournisseur.", parent=form)
        self.button(form, "Obtenir ma clé sur console.groq.com", lambda: webbrowser.open("https://console.groq.com/keys")).pack(anchor="w", pady=(0, 10))
        self.label(form, "Clé API Groq (masquée)", muted=True).pack(anchor="w")
        self.key_var = tk.StringVar()
        field = self.entry(form, self.key_var)
        field.configure(show="•")
        field.pack(fill="x", ipady=7, pady=(4, 10))
        self.label(form, "Modèle Groq", muted=True).pack(anchor="w")
        self.model_var = tk.StringVar(value=self.settings.model)
        self.entry(form, self.model_var).pack(fill="x", ipady=7, pady=(4, 10))
        self.persist_var = tk.BooleanVar(value=False)
        tk.Checkbutton(form, text="Mémoriser la clé dans le coffre sécurisé du système (facultatif)", variable=self.persist_var,
                       bg=self.BG, fg=self.FG, selectcolor=self.PANEL, activebackground=self.BG, activeforeground=self.FG).pack(anchor="w")
        bar = tk.Frame(form, bg=self.BG)
        bar.pack(fill="x", pady=10)
        for title, command in (("Tester et connecter", self.connect_ai), ("Charger du coffre", self.load_vault), ("Déconnecter", self.disconnect_ai)):
            self.button(bar, title, command).pack(side="left", padx=(0, 8))
        self.paragraph("État : " + ("clé disponible pour cette session" if self.settings.has_api_key() else "IA déconnectée") + ". Le test contacte uniquement Groq pour vérifier l’accès au modèle.", parent=form)
        self.label(form, "Dossiers autorisés pour Documents", 12, True).pack(anchor="w", pady=(10, 6))
        self.roots_list = self.listbox(form)
        self.roots_list.pack(fill="both", expand=True)
        for root in self.settings.roots:
            self.roots_list.insert("end", str(root))
        self.button(form, "Retirer le dossier sélectionné", self.forget_root).pack(anchor="w", pady=8)


    def connect_ai(self):
        if self.busy:
            return
        try:
            key = self.key_var.get().strip() or self.settings.get_api_key()
            model = self.model_var.get().strip()
            persist = self.persist_var.get()
            client = create_client(key, model)
        except GroqError as error:
            self.show_result(str(error), "Connexion non établie")
            return
        def done(_):
            previous_model = self.settings.model
            try:
                self.settings.model = model
                try:
                    self.settings.save()
                except ConfigurationError:
                    self.settings.model = previous_model
                    raise
                self.settings.set_api_key(key, persist=persist)
                self.chat_consent = False
                self.key_var.set("")
                self.navigate("Configuration", force=True)
                self.status.set("Groq connecté · Clé dans le coffre" if persist else "Groq connecté · Clé en mémoire jusqu’à la fermeture")
            except ConfigurationError as error:
                self.key_var.set("")
                self.show_result(str(error), "Configuration à vérifier")
        self.run_job(client.validate, done, "Vérification de la connexion Groq…", kind="configuration")

    def load_vault(self):
        if self.busy:
            return
        try:
            self.settings.use_vault()
            self.chat_consent = False
            self.navigate("Configuration", force=True)
            self.status.set("Clé chargée du coffre · Vous pouvez tester la connexion")
        except ConfigurationError as error:
            self.show_result(str(error), "Coffre indisponible")

    def disconnect_ai(self):
        if self.busy:
            return
        delete = messagebox.askyesnocancel("Déconnecter Groq", "Supprimer aussi une éventuelle clé Community du coffre ?\n\nOui : mémoire et coffre. Non : mémoire seulement.", parent=self)
        if delete is None:
            return
        self.settings.forget_memory()
        self.chat_consent = False
        warning = ""
        if delete:
            try:
                self.settings.clear_api_key()
            except ConfigurationError as error:
                warning = str(error)
        self.navigate("Configuration", force=True)
        self.show_result(warning or "La clé en mémoire a été effacée.", "IA déconnectée")

    def forget_root(self):
        if self.busy:
            return
        selection = self.roots_list.curselection()
        if not selection:
            return
        try:
            self.settings.forget_root(self.roots_list.get(selection[0]))
            # Discard document snapshot when revoking authorization.
            self.file_path, self.file_content = None, ""
            self.navigate("Configuration", force=True)
        except ConfigurationError as error:
            self.show_result(str(error), "Autorisation inchangée")

    def search(self):
        if self.busy:
            return
        text = self.action_text()
        if text is None:
            return
        query = simpledialog.askstring("Rechercher", "Mot, expression ou question :", parent=self)
        if query is None or not query.strip():
            return
        if self.settings.has_api_key() and messagebox.askyesno("Mode de recherche", "Utiliser l’IA pour répondre à cette question ?\n\nNon : rechercher localement les mots exacts.", parent=self):
            self.ai_action("search", text=text, question=query)
        else:
            try:
                self.show_result(search_text(text, query), "Recherche locale · Aucun envoi")
            except ValueError as error:
                self.show_result(str(error), "Recherche impossible")

    def summarize(self):
        self.ai_action("summary")

    def extract(self):
        self.ai_action("extract")

    def ai_action(self, purpose, text=None, question=""):
        if self.busy:
            return
        text = self.action_text() if text is None else text
        if text is None:
            return
        if len(text) > MAX_INPUT:
            self.show_result("Sélectionnez un extrait de 60 000 caractères maximum. Aucun texte n’a été envoyé.", "Texte trop long")
            return
        try:
            client = self.client()
        except GroqError as error:
            self.show_result(str(error), "IA facultative · Connectez votre fournisseur")
            return
        source = self.source_context()
        if not messagebox.askyesno("Autoriser l’analyse IA", f"Envoyer ce texte à Groq pour cette action ?\n\nSource : {source}\nTaille : {len(text):,} caractères\n\nLa sélection est utilisée si elle existe, sinon tout le texte affiché. Vérifiez qu’il ne contient pas de données que vous souhaitez garder privées.", parent=self):
            return
        self.run_job(lambda: analyze(client, purpose, text, question),
                     lambda answer: self.show_result(answer, "Réponse Groq · " + source + " · À vérifier"),
                     "Analyse Groq en cours…")

    def backup_data(self):
        if not self.leave_note():
            return
        filename = filedialog.asksaveasfilename(parent=self, title="Sauvegarder notes et tâches",
            defaultextension=".json", initialfile="sowilo-community-sauvegarde.json", filetypes=(("Sauvegarde Community", "*.json"),))
        if filename:
            ok, _ = self.run_data(lambda: save_backup(self.store, filename))
            if ok:
                self.status.set("Notes et tâches sauvegardées · Fichier privé non chiffré")

    def restore_data(self):
        if self.busy:
            self.status.set("Attendez la fin du traitement avant de restaurer")
            return
        if not self.leave_note():
            return
        filename = filedialog.askopenfilename(parent=self, title="Restaurer une sauvegarde Community",
                                              filetypes=(("Sauvegarde Community", "*.json"),))
        if not filename:
            return
        ok, payload = self.run_data(lambda: read_backup(filename))
        if not ok:
            return
        if not messagebox.askyesno("Remplacer les notes et tâches", f"Restaurer {len(payload['notes'])} note(s) et {len(payload['tasks'])} tâche(s) ?\n\nCela remplacera vos notes et tâches actuelles. Une copie de sécurité sera créée avant le remplacement. Fermez les autres fenêtres Community. Les clés et documents externes ne seront pas modifiés.", parent=self):
            return
        ok, safety = self.run_data(lambda: restore_backup(self.store, payload, self.settings.paths.data_dir / "backups"))
        if ok:
            self.note_id = None
            self.note_revision = None
            self.note_snapshot = ("", "")
            self.page = None
            self.navigate("Accueil", force=True)
            self.show_result("Restauration terminée. Copie des données précédentes :\n" + str(safety), "Notes et tâches restaurées")

    def export_data(self):
        if not self.leave_note():
            return
        directory = filedialog.askdirectory(parent=self, title="Exporter vos notes en Markdown")
        if directory:
            ok, destination = self.run_data(lambda: export_notes(self.store, directory))
            if ok:
                self.show_result("Notes exportées dans :\n" + str(destination), "Export Markdown terminé")

    def build_guide(self):
        form = self.scroll_form()
        step = self.settings.guide_step
        title, text, action, target = GUIDE[step]
        self.label(form, f"ÉTAPE {step + 1} / {len(GUIDE)} · {title}", 15, True).pack(anchor="w", pady=(0, 18))
        self.paragraph(text, parent=form)
        command = self.open_example if target == "Exemple" else lambda: self.navigate(target)
        self.button(form, action, command, True).pack(anchor="w", pady=8)
        if step == 2:
            self.button(form, "Essayer les tâches", lambda: self.navigate("Tâches")).pack(anchor="w", pady=4)
            self.button(form, "Lire le document d’exemple", self.open_example).pack(anchor="w", pady=4)
        bar = tk.Frame(form, bg=self.BG)
        bar.pack(fill="x", pady=22)
        if step:
            self.button(bar, "Précédent", lambda: self.guide_change(step - 1)).pack(side="left", padx=(0, 8))
        self.button(bar, "Terminer le guide" if step == 3 else "Suivant / Passer cette étape",
                    lambda: self.guide_change(step + 1)).pack(side="left", padx=(0, 8))
        self.button(bar, "Plus tard", self.guide_dismiss).pack(side="left")
        self.paragraph("Vos conversations restent en mémoire jusqu’à fermeture. Les notes et tâches sont conservées localement.\n\nAucune action IA n’exécute de commande, n’envoie d’email ou ne modifie vos documents.\n\nV1 Linux · Pas d’OCR ni de voix. TTS prévu pour la V2, STT à étudier.", parent=form)
        self.paragraph("Données : " + str(self.settings.paths.data_dir) + "\nConfiguration : " + str(self.settings.paths.config_file), parent=form)
        self.button(form, "Recommencer le guide", lambda: self.guide_change(0)).pack(anchor="w")


    def guide_change(self, step):
        previous = (self.settings.guide_step, self.settings.guide_completed, self.settings.guide_dismissed)
        self.settings.guide_step = min(step, 3)
        self.settings.guide_completed = step >= 4
        self.settings.guide_dismissed = step >= 4
        try:
            self.settings.save()
        except ConfigurationError as error:
            self.settings.guide_step, self.settings.guide_completed, self.settings.guide_dismissed = previous
            self.show_result(str(error), "Progression non enregistrée")
            return
        self.navigate("Accueil" if step >= 4 else "Aide", force=True)

    def guide_dismiss(self):
        self.settings.guide_dismissed = True
        try:
            self.settings.save()
        except ConfigurationError as error:
            self.settings.guide_dismissed = False
            self.show_result(str(error), "Progression non enregistrée")
            return
        self.navigate("Accueil")

    def close(self):
        if self.busy and not messagebox.askyesno("Traitement en cours", "Fermer malgré l’opération en cours ? Un texte déjà envoyé au fournisseur ne peut pas être rappelé.", parent=self):
            return
        if not self.leave_note():
            return
        self.settings.forget_memory()
        if self.store is not None:
            self.store.close()
        self.destroy()
