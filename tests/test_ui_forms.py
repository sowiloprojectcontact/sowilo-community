"""Construct the real Community views with simulated widgets (no display)."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from community.app import CommunityApp


class Widget:
    def __init__(self, parent=None, **kwargs):
        self.options=kwargs
        self.value=''
        self.items=[]
        self.children=[]
        if isinstance(parent,Widget):parent.children.append(self)
    def pack(self, **kwargs):pass
    def pack_propagate(self,*args):pass
    def grid(self,**kwargs):pass
    def columnconfigure(self,*args,**kwargs):pass
    def bind(self,*args):pass
    def configure(self,**kwargs):self.options.update(kwargs)
    def cget(self,key):return self.options.get(key,'#000')
    def tag_configure(self,*args,**kwargs):pass
    def insert(self,index,value,*tags):self.value+=str(value);self.items.append(value)
    def delete(self,*args):self.value='';self.items=[]
    def see(self,*args):pass
    def set(self,*args):pass
    def yview(self,*args):pass
    def get(self,*args):return self.value
    def create_window(self,*args,**kwargs):return 1
    def bbox(self,*args):return (0,0,700,1000)
    def itemconfigure(self,*args,**kwargs):pass


class Variable:
    def __init__(self, value=None, **kwargs):self.value=value
    def get(self):return self.value
    def set(self,value):self.value=value


class FormsTests(unittest.TestCase):
    def setUp(self):
        self.fake=SimpleNamespace(BG='#000',PANEL='#111',FG='#fff',MUTED='#aaa',PURPLE='#a7f',
            content=Widget(),settings=SimpleNamespace(model='model',has_api_key=lambda:False,
                roots=('/tmp/documents',),guide_step=0,paths=SimpleNamespace(data_dir='/tmp/data',config_file='/tmp/config')),
            file_path=None,file_content='',chat_draft='',chat_messages=[],status=Variable(),
            navigate=Mock(),open_example=Mock(),guide_change=Mock(),guide_dismiss=Mock(),
            busy=False,job_kind=None,copy_response=Mock(),response_to_note=Mock(),response_to_task=Mock(),
            backup_data=Mock(),restore_data=Mock(),export_data=Mock(),
            connect_ai=Mock(),load_vault=Mock(),disconnect_ai=Mock(),forget_root=Mock(),
            send_chat=Mock(),reset_chat=Mock(),open_document=Mock())
        for method in ('scroll_form','paragraph','render_chat'):
            setattr(self.fake,method,getattr(CommunityApp,method).__get__(self.fake))
        self.fake.panel=lambda parent,**kwargs:(Widget(parent),Widget(parent))
        self.fake.label=lambda parent,text,*args,**kwargs:Widget(parent,text=text)
        self.fake.button=lambda parent,text,command,*args,**kwargs:Widget(parent,text=text,command=command)
        self.fake.text_area=lambda parent,*args:Widget(parent)
        self.fake.entry=lambda parent,*args:Widget(parent)
        self.fake.listbox=lambda parent:Widget(parent)
        for name in ('Frame','Canvas','Scrollbar','Label','Checkbutton'):
            p=patch('community.app.tk.'+name,Widget);p.start();self.addCleanup(p.stop)
        for name in ('StringVar','BooleanVar'):
            p=patch('community.app.tk.'+name,Variable);p.start();self.addCleanup(p.stop)

    def test_settings_constructs_real_connect_fields_and_roots(self):
        CommunityApp.build_settings(self.fake)
        self.assertEqual(self.fake.model_var.get(),'model')
        self.assertEqual(self.fake.roots_list.items,['/tmp/documents'])
        self.assertEqual(self.fake.key_var.get(),None)
        self.assertFalse(self.fake.persist_var.get())

    def test_shell_exposes_personal_tools_and_navigation_callbacks(self):
        for name in ('show_result', 'hide_result', 'summarize', 'search', 'extract', 'bind'):
            setattr(self.fake, name, Mock())
        self.fake.last_result = ''
        with patch('community.app.rune', return_value=Widget()):
            CommunityApp.build_shell(self.fake)
        pages = ['Accueil', 'Notes', 'Tâches', 'Documents', 'Chat', 'Configuration', 'Aide']
        self.assertEqual(list(self.fake.nav_buttons), pages)
        for page, button in self.fake.nav_buttons.items():
            button.options['command']()
            self.fake.navigate.assert_called_with(page)

    def test_guide_constructs_every_step_and_real_navigation_command(self):
        def all_widgets(widget):
            yield widget
            for child in widget.children:yield from all_widgets(child)
        for step in range(4):
            self.fake.content=Widget()
            self.fake.settings.guide_step=step
            CommunityApp.build_guide(self.fake)
            buttons={w.options.get('text'):w for w in all_widgets(self.fake.content) if 'command' in w.options}
            label='Terminer le guide' if step==3 else 'Suivant / Passer cette étape'
            buttons[label].options['command']()
            self.fake.guide_change.assert_called_with(step+1)

    def test_documents_view_preserves_loaded_snapshot(self):
        self.fake.file_content='Example document'
        CommunityApp.build_documents(self.fake)
        self.assertEqual(self.fake.file_editor.value,'Example document')
        self.assertEqual(self.fake.file_editor.options['state'],'disabled')
        self.assertIs(self.fake.source_editor,self.fake.file_editor)

    def test_chat_restores_history_and_draft(self):
        self.fake.chat_messages=[{'role':'user','content':'Question'},{'role':'assistant','content':'Answer'}]
        self.fake.chat_draft='Unsent'
        CommunityApp.build_chat(self.fake)
        self.assertIn('Answer',self.fake.chat_output.value)
        self.assertEqual(self.fake.chat_input.value,'Unsent')


if __name__=='__main__':unittest.main()
