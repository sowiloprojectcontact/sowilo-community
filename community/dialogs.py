"""Explicit review before turning a response into local user data."""
import tkinter as tk
from tkinter import simpledialog
from tkinter.scrolledtext import ScrolledText
from sowilo_data import MAX_TEXT_BYTES
from .theme import BG, PANEL, FG, FONT, NEON


class NoteReview(simpledialog.Dialog):
    def __init__(self, parent, content):
        self.content=content
        super().__init__(parent,title='Relire et enregistrer une note')

    def body(self, master):
        master.configure(bg=BG)
        tk.Label(master,text='Relisez et modifiez le texte avant de l’enregistrer.',bg=BG,fg=FG).pack(anchor='w')
        self.title_field=tk.Entry(master,width=60,bg=PANEL,fg=FG,insertbackground=NEON)
        self.title_field.insert(0,'Réponse Sowilo')
        self.title_field.pack(fill='x',pady=8)
        self.editor=ScrolledText(master,width=65,height=16,wrap='word',bg=PANEL,fg=FG,
                                 insertbackground=NEON,font=(FONT,11))
        self.editor.insert('1.0',self.content)
        self.editor.pack(fill='both',expand=True)
        return self.title_field

    def validate(self):
        title=self.title_field.get().strip()
        content=self.editor.get('1.0','end-1c')
        return bool(title) and len(title)<=300 and len(content.encode('utf-8'))<=MAX_TEXT_BYTES

    def apply(self):
        self.result=(self.title_field.get().strip(),self.editor.get('1.0','end-1c'))
