"""Cross-view completions and explicit data reuse, without real network or data."""
from pathlib import Path
import queue
from types import SimpleNamespace
import tkinter as tk
import unittest
from unittest.mock import Mock,patch
from community.app import CommunityApp


class UpgradeFlowTests(unittest.TestCase):
    def fake(self):
        fake=SimpleNamespace(page='Chat',busy=False,job_kind=None,chat_messages=[],chat_consent=True,
            chat_draft='',last_chat_output='',last_result='',chat_input=Mock(),chat_output=Mock(),
            client=Mock(return_value=Mock()),run_job=Mock(),after=Mock(),restore_chat_input=Mock(),
            render_chat=Mock(),status=Mock(),show_result=Mock(),refresh_actions=Mock(),
            source_editor=None,file_path=Path('/tmp/demo.txt'),task_rows=[],action_bar=Mock(),
            settings=SimpleNamespace(has_api_key=lambda:True))
        return fake

    def test_chat_finishing_on_other_view_never_touches_destroyed_widgets(self):
        fake=self.fake();fake.chat_input.get.return_value='Question'
        CommunityApp.send_chat(fake)
        _,done,_=fake.run_job.call_args.args
        self.assertEqual(fake.run_job.call_args.kwargs,{'kind':'chat'})
        fake.page='Notes'
        fake.chat_input.reset_mock()
        done('Answer')
        self.assertEqual(fake.last_chat_output,'Answer')
        self.assertEqual(fake.chat_draft,'')
        fake.chat_input.configure.assert_not_called()
        fake.chat_input.delete.assert_not_called()
        fake.render_chat.assert_not_called()

    def test_navigation_to_notes_allowed_while_chat_is_running(self):
        fake=self.fake();fake.busy=True;fake.job_kind='chat'
        fake.leave_note=Mock(return_value=True);fake.hide_result=Mock()
        fake.content=Mock();fake.content.winfo_children.return_value=[]
        fake.nav_buttons={};fake.label=Mock();fake.build_notes=Mock()
        for name in ('build_home','build_tasks','build_documents','build_chat','build_settings','build_guide'):
            setattr(fake,name,Mock())
        CommunityApp.navigate(fake,'Notes')
        self.assertEqual(fake.page,'Notes')
        fake.build_notes.assert_called_once()
        fake.hide_result.assert_called_once()

    def test_chat_error_on_another_view_preserves_retry_draft(self):
        fake=self.fake();fake.busy=True;fake.job_kind='chat';fake.page='Notes'
        fake.chat_draft='Retry this';fake.jobs=queue.Queue()
        done=Mock();fake.jobs.put((False,'Network unavailable',done))
        CommunityApp.poll_job(fake)
        self.assertFalse(fake.busy)
        self.assertEqual(fake.chat_draft,'Retry this')
        self.assertEqual(fake.chat_messages,[])
        fake.chat_input.configure.assert_not_called();done.assert_not_called()

    def test_context_distinguishes_selected_text_and_whole_document(self):
        fake=self.fake();fake.page='Documents';fake.source_editor=Mock()
        fake.source_editor.get.return_value='Extract'
        self.assertEqual(CommunityApp.source_context(fake),'Sélection · demo.txt')
        fake.source_editor.get.side_effect=tk.TclError('no selection')
        self.assertEqual(CommunityApp.source_context(fake),'Document entier · demo.txt')

    def test_actions_disabled_for_empty_source_and_disconnected_ai(self):
        fake=self.fake();fake.page='Notes';fake.source_editor=Mock()
        fake.source_editor.get.return_value='';fake.source_editor.compare.return_value=False
        fake.action_buttons={name:Mock() for name in ('Résumer','Rechercher','Extraire')}
        CommunityApp.refresh_actions(fake)
        for button in fake.action_buttons.values():button.configure.assert_called_with(state='disabled')
        fake.source_editor.get.return_value='Note'
        fake.settings.has_api_key=lambda:False
        CommunityApp.refresh_actions(fake)
        fake.action_buttons['Rechercher'].configure.assert_called_with(state='normal')
        fake.action_buttons['Résumer'].configure.assert_called_with(state='disabled')

    def test_chat_hides_irrelevant_document_actions(self):
        fake=self.fake();fake.action_buttons={}
        CommunityApp.refresh_actions(fake)
        fake.action_bar.pack_forget.assert_called_once()

    def test_reuse_uses_latest_answer_unless_user_selected_text(self):
        fake=self.fake();fake.last_chat_output='Complete answer'
        fake.chat_output.get.side_effect=tk.TclError('no selection')
        self.assertEqual(CommunityApp.reusable_text(fake),'Complete answer')
        fake.chat_output.get.side_effect=None;fake.chat_output.get.return_value='Selected'
        self.assertEqual(CommunityApp.reusable_text(fake),'Selected')

    def test_creating_note_requires_review_and_keeps_existing_draft(self):
        fake=self.fake();fake.page='Notes';fake.reusable_text=Mock(return_value='AI output')
        fake.store=Mock();fake.refresh_notes=Mock();fake.run_data=Mock(return_value=(True,1))
        with patch('community.app.NoteReview',return_value=SimpleNamespace(result=None)):
            CommunityApp.response_to_note(fake)
        fake.run_data.assert_not_called()
        with patch('community.app.NoteReview',return_value=SimpleNamespace(result=('Reviewed','Corrected text'))):
            CommunityApp.response_to_note(fake)
        fake.run_data.call_args.args[0]()
        fake.store.save_note.assert_called_once_with('Reviewed','Corrected text')
        fake.chat_input.delete.assert_not_called()

    def test_task_creation_cancelled_does_not_write(self):
        fake=self.fake();fake.reusable_text=Mock(return_value='An action');fake.run_data=Mock()
        with patch('community.app.simpledialog.askstring',return_value=None):
            CommunityApp.response_to_task(fake)
        fake.run_data.assert_not_called()

    def test_result_is_reopenable_after_collapsing(self):
        fake=self.fake();fake.result=Mock();fake.result_toggle=Mock();fake.result_container=Mock();fake.status_widget=Mock()
        CommunityApp.show_result(fake,'Answer','Ready')
        self.assertEqual(fake.last_result,'Answer')
        fake.result_toggle.configure.assert_called_with(state='normal')
        CommunityApp.hide_result(fake)
        fake.result_container.pack_forget.assert_called_once()
        self.assertEqual(fake.last_result,'Answer')

    def test_global_result_reuse_does_not_pick_an_unrelated_chat_answer(self):
        fake=self.fake();fake.last_result='Document summary';fake.last_chat_output='Other answer'
        fake.result=Mock();fake.result.get.side_effect=tk.TclError('no selection')
        self.assertEqual(CommunityApp.reusable_text(fake,from_result=True),'Document summary')
