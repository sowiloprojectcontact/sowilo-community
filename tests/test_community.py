"""Community integration contracts: isolated data, fake AI, no network or display."""
import importlib.util
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, MagicMock, patch
from urllib.error import HTTPError, URLError

from community.ai import analyze, prepare_chat, create_client, MAX_INPUT
from community.app import CommunityApp
from community.config import AppConfig, ConfigurationError, _secure_vault
from community.groq import GroqClient, GroqError, NoRedirect
from community.paths import AppPaths
from sowilo_data import Store

ROOT = Path(__file__).resolve().parent.parent


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.paths = AppPaths(root/'config', root/'data', root/'data/documents', root/'config/config.json')
        self.paths.ensure()
        self.config = AppConfig(self.paths)

    def test_namespace_and_relative_xdg_fallback(self):
        with patch.dict(os.environ, {'XDG_CONFIG_HOME':'relative', 'XDG_DATA_HOME':'/tmp/community-data'}):
            paths = AppPaths.discover()
        self.assertEqual(paths.config_dir, Path.home()/'.config/sowilo-community')
        self.assertEqual(paths.data_dir, Path('/tmp/community-data/sowilo-community'))

    def test_secret_never_serialized_and_guide_survives_restart(self):
        self.config.set_api_key('TEST-SECRET-NOT-REAL')
        self.config.guide_step = 2
        self.config.guide_dismissed = True
        self.config.save()
        raw = self.paths.config_file.read_text()
        self.assertNotIn('SECRET', raw)
        second = AppConfig(self.paths)
        second.load()
        self.assertEqual(second.guide_step, 2)
        self.assertTrue(second.guide_dismissed)
        with patch('community.config._secure_vault') as vault:
            self.assertFalse(second.has_api_key())
            vault.assert_not_called()
        self.assertEqual(self.paths.config_file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.paths.data_dir.stat().st_mode & 0o777, 0o700)

    def test_existing_configuration_error_not_overwritten(self):
        self.paths.config_file.write_text('{broken')
        with self.assertRaises(ConfigurationError):self.config.load()
        self.assertEqual(self.paths.config_file.read_text(), '{broken')

    def test_invalid_config_values_rejected(self):
        for payload in ({'guide_step':True}, {'guide_step':4}, {'model':'a b'}, {'guide_completed':'yes'}, {'roots':[42]}, []):
            self.paths.config_file.write_text(json.dumps(payload))
            with self.assertRaises(ConfigurationError):AppConfig(self.paths).load()

    def test_root_authorization_and_revocation(self):
        extra = Path(self.temp.name)/'external';extra.mkdir()
        self.config.authorize_root(extra)
        restored = AppConfig(self.paths);restored.load()
        self.assertIn(extra, restored.roots)
        restored.forget_root(extra)
        self.assertNotIn(extra, restored.roots)
        with self.assertRaises(ConfigurationError):restored.forget_root(self.paths.documents_dir)
        self.assertTrue(extra.exists())

    def test_failed_root_save_rolls_back(self):
        roots = self.config.roots
        with patch.object(self.config, 'save', side_effect=ConfigurationError('failed')):
            with self.assertRaises(ConfigurationError):self.config.authorize_root(Path(self.temp.name))
        self.assertEqual(roots, self.config.roots)

    def test_config_symlink_rejected(self):
        target=Path(self.temp.name)/'untouched';target.write_text('original')
        self.paths.config_file.symlink_to(target)
        with self.assertRaises(ConfigurationError):self.config.save()
        self.assertEqual(target.read_text(), 'original')

    def test_key_uses_community_vault_only_on_opt_in(self):
        backend = Mock();backend.get_password.return_value = 'FROM-VAULT'
        with patch('community.config._secure_vault', return_value=backend):
            self.config.set_api_key('MEMORY', persist=False)
            backend.set_password.assert_not_called()
            self.config.set_api_key('PERSIST', persist=True)
            backend.set_password.assert_called_once_with('Sowilo Community','groq_api_key','PERSIST')
            self.config.forget_memory()
            self.assertEqual(self.config.get_api_key(),'')
            self.config.use_vault()
            self.assertEqual(self.config.get_api_key(),'FROM-VAULT')
            self.config.clear_api_key()
            self.assertEqual(self.config.get_api_key(),'')
            backend.delete_password.assert_called_once()

    def test_no_environment_credential_import(self):
        with patch.dict(os.environ, {'GROQ_API_KEY':'DO-NOT-IMPORT'}), patch('community.config._secure_vault') as vault:
            self.assertEqual(self.config.get_api_key(),'')
            vault.assert_not_called()

    def test_vault_failure_keeps_key_in_memory_but_not_disk(self):
        with patch('community.config._secure_vault', side_effect=RuntimeError('SECRET')):
            with self.assertRaises(ConfigurationError) as error:self.config.set_api_key('MEMORY',persist=True)
        self.assertNotIn('SECRET',str(error.exception))
        self.assertEqual(self.config.get_api_key(),'MEMORY')
        self.config.save()
        self.assertNotIn('MEMORY', self.paths.config_file.read_text())

    def test_vault_errors_are_safe(self):
        backend = Mock();backend.get_password.side_effect=RuntimeError('SECRET')
        with patch('community.config._secure_vault', return_value=backend):
            with self.assertRaises(ConfigurationError) as error:self.config.use_vault()
        self.assertNotIn('SECRET', str(error.exception))

    def test_plaintext_and_chained_vault_rejected(self):
        backend=type('Unsafe', (), {'priority':1})()
        fake=SimpleNamespace(get_keyring=lambda:backend)
        with patch.dict(sys.modules, {'keyring':fake}):
            with self.assertRaises(ConfigurationError):_secure_vault()

    def test_local_database_independent_from_source(self):
        db=self.paths.data_dir/'community.sqlite3'
        store=Store(db)
        store.save_note('Community','Independent')
        store.close()
        self.assertTrue(db.exists())
        self.assertNotIn('sowilo_mini',str(db))


class AITests(unittest.TestCase):
    def test_provider_interface_only_exposes_available_connector(self):
        self.assertIsInstance(create_client('test-key','model'),GroqClient)
        with self.assertRaises(GroqError):create_client('test-key','model',provider='claude')

    def test_chat_limits_and_history_not_modified(self):
        history=[{'role':'assistant','content':'Bonjour'}]
        pending=prepare_chat(history,'  Question  ')
        self.assertEqual(len(history),1)
        self.assertEqual(pending[-1]['content'],'Question')
        for text in ('', ' '*10,'x'*16001):
            with self.assertRaises(ValueError):prepare_chat([],text)
        with self.assertRaises(ValueError):prepare_chat([{'role':'assistant','content':'x'*MAX_INPUT}], 'next')

    def test_ai_receives_only_explicit_source(self):
        client=Mock();client.complete.return_value='Result'
        self.assertEqual(analyze(client,'search','Public text','Question?'),'Result')
        messages=client.complete.call_args.args[0]
        self.assertEqual(len(messages),2)
        self.assertIn('Public text',messages[1]['content'])
        self.assertIn('Question?',messages[1]['content'])
        self.assertIn('aucun accès',messages[0]['content'])

    def test_ai_limits_fail_before_network(self):
        client=Mock()
        for purpose,text,question in [('summary','x'*(MAX_INPUT+1),''),('search','text',''),('extract','',''),('unknown','text','')]:
            with self.assertRaises(ValueError):analyze(client,purpose,text,question)
        client.complete.assert_not_called()

    def test_redirect_does_not_forward_authentication(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'move',{},'https://other.example'))

    def client_response(self, payload):
        client=GroqClient('fake-key','model')
        response=Mock();response.read.return_value=json.dumps(payload).encode()
        client.opener=MagicMock();client.opener.open.return_value.__enter__.return_value=response
        return client

    def test_request_uses_fixed_endpoint_and_bounded_timeout(self):
        client=self.client_response({'choices':[{'message':{'content':'Bonjour'}}]})
        self.assertEqual(client.complete([{'role':'user','content':'Hi'}]),'Bonjour')
        args,kwargs=client.opener.open.call_args
        self.assertEqual(args[0].full_url,'https://api.groq.com/openai/v1/chat/completions')
        self.assertEqual(kwargs['timeout'],35)

    def test_invalid_empty_and_large_responses(self):
        for data in ({}, {'choices':[]},{'choices':[{'message':{'content':''}}]}, []):
            with self.assertRaises(GroqError):self.client_response(data).complete([])
        client=self.client_response({})
        client.opener.open.return_value.__enter__.return_value.read.return_value=b'x'*(4*1024*1024+1)
        with self.assertRaises(GroqError):client.complete([])

    def test_network_errors_never_leak_secrets(self):
        for error in (URLError('fake-key'),HTTPError('https://x',401,'fake-key',{},None),TimeoutError('fake-key')):
            client=GroqClient('fake-key','model');client.opener=Mock();client.opener.open.side_effect=error
            with self.assertRaises(GroqError) as caught:client.validate()
            self.assertNotIn('fake-key',str(caught.exception))

    def test_model_availability_test(self):
        self.assertTrue(self.client_response({'data':[{'id':'model'}]}).validate())
        with self.assertRaises(GroqError):self.client_response({'data':[{'id':'other'}]}).validate()


class UIContracts(unittest.TestCase):
    def fake(self, **overrides):
        fake=SimpleNamespace(busy=False,status=Mock(),show_result=Mock(),navigate=Mock(),
                             refresh_actions=Mock(),job_kind=None,source_context=Mock(return_value="Document entier · doc.txt"),
                             settings=Mock(),page='Documents',file_path=Path('/tmp/doc.txt'),
                             action_text=Mock(return_value='SOURCE'),client=Mock(return_value=Mock()),run_job=Mock())
        for k,v in overrides.items():setattr(fake,k,v)
        return fake

    def test_declining_document_consent_sends_nothing(self):
        fake=self.fake()
        with patch('community.app.messagebox.askyesno',return_value=False):CommunityApp.ai_action(fake,'summary')
        fake.run_job.assert_not_called()

    def test_empty_or_oversized_content_never_sends(self):
        for text in (None,'x'*(MAX_INPUT+1)):
            fake=self.fake(action_text=Mock(return_value=text))
            CommunityApp.ai_action(fake,'summary')
            fake.run_job.assert_not_called()

    def test_approved_document_action_uses_captured_text(self):
        fake=self.fake()
        with patch('community.app.messagebox.askyesno',return_value=True):CommunityApp.ai_action(fake,'extract')
        work,done,_=fake.run_job.call_args.args
        with patch('community.app.analyze',return_value='Answer') as analyze_mock:
            work();analyze_mock.assert_called_once_with(fake.client.return_value,'extract','SOURCE','')
        done('Answer');fake.show_result.assert_called_once()

    def test_missing_key_does_not_prompt_send(self):
        fake=self.fake(client=Mock(side_effect=GroqError('Connect first')))
        with patch('community.app.messagebox.askyesno') as confirm:CommunityApp.ai_action(fake,'summary')
        confirm.assert_not_called();fake.run_job.assert_not_called()

    def test_guide_progress_persists_and_can_restart(self):
        settings=SimpleNamespace(guide_step=2,guide_completed=False,guide_dismissed=False,save=Mock())
        fake=self.fake(settings=settings)
        CommunityApp.guide_change(fake,4)
        self.assertTrue(settings.guide_completed)
        fake.navigate.assert_called_with('Accueil',force=True)
        CommunityApp.guide_change(fake,0)
        self.assertFalse(settings.guide_completed)
        self.assertFalse(settings.guide_dismissed)

    def test_guide_save_error_does_not_advance(self):
        settings=SimpleNamespace(guide_step=1,guide_completed=False,guide_dismissed=False,save=Mock(side_effect=ConfigurationError('Fail')))
        fake=self.fake(settings=settings)
        CommunityApp.guide_change(fake,2)
        self.assertEqual(settings.guide_step,1);fake.navigate.assert_not_called()

    def test_background_work_never_updates_tk_from_worker(self):
        main_thread=threading.get_ident();done=Mock();completed=threading.Event();jobs=queue.Queue()
        fake=self.fake(jobs=jobs,after=Mock(),poll_job=Mock())
        def work():
            self.assertNotEqual(threading.get_ident(),main_thread)
            completed.set();return 'Answer'
        CommunityApp.run_job(fake,work,done,'Running')
        self.assertTrue(completed.wait(2))
        self.assertTrue(fake.busy);done.assert_not_called()
        CommunityApp.poll_job(fake)
        self.assertFalse(fake.busy);done.assert_called_once_with('Answer')

    def test_background_error_redacted_and_done_not_called(self):
        done=Mock();jobs=queue.Queue();finished=threading.Event()
        fake=self.fake(jobs=jobs,after=Mock(),poll_job=Mock())
        def work():
            try:raise RuntimeError('PRIVATE-SECRET')
            finally:finished.set()
        CommunityApp.run_job(fake,work,done,'Running')
        self.assertTrue(finished.wait(2))
        success,result,callback=jobs.get(timeout=2)
        self.assertFalse(success);self.assertNotIn('PRIVATE-SECRET',result)
        jobs.put((success,result,callback));CommunityApp.poll_job(fake)
        done.assert_not_called();fake.show_result.assert_called_once()

    def test_navigation_blocked_during_pending_result(self):
        fake=self.fake(busy=True,job_kind="configuration")
        CommunityApp.navigate(fake,'Configuration')
        fake.status.set.assert_called_once()

    def test_document_outside_scope_requires_permission(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'note.txt';path.write_text('Private')
            settings=SimpleNamespace(roots=(),authorize_root=Mock())
            fake=self.fake(settings=settings)
            with patch('community.app.messagebox.askyesno',return_value=False):CommunityApp.load_document(fake,path)
            settings.authorize_root.assert_not_called();fake.run_job.assert_not_called()

    def test_bundled_example_exception_does_not_accept_arbitrary_file(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'note.txt';path.write_text('Private')
            fake=self.fake()
            CommunityApp.load_document(fake,path,example=True)
            fake.run_job.assert_not_called()


class LaunchTests(unittest.TestCase):
    def test_import_and_check_do_not_touch_user_storage_or_network(self):
        with tempfile.TemporaryDirectory() as d:
            env=dict(os.environ,XDG_CONFIG_HOME=d+'/config',XDG_DATA_HOME=d+'/data')
            result=subprocess.run([sys.executable,str(ROOT/'main.py'),'--check'],env=env,cwd='/tmp',capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(list(Path(d).iterdir()),[])

    def test_moved_source_tree_runs_without_original_sources(self):
        with tempfile.TemporaryDirectory(prefix='community moved ') as d:
            dest=Path(d)/'Sowilo Community';dest.mkdir()
            for name in ('main.py','sowilo_mini.py','sowilo_data.py','community','modules','examples','launch.sh'):
                source=ROOT/name
                if source.is_dir():shutil.copytree(source,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
                else:shutil.copy2(source,dest/name)
            env=dict(os.environ,XDG_CONFIG_HOME=d+'/config',XDG_DATA_HOME=d+'/data')
            result=subprocess.run([sys.executable,str(dest/'main.py'),'--check'],env=env,cwd='/tmp',capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(Path(d+'/config').exists())
            self.assertFalse(Path(d+'/data').exists())


if __name__=='__main__':unittest.main()


class ChatAndSettingsContracts(unittest.TestCase):
    def fake(self):
        return SimpleNamespace(busy=False,page='Chat',chat_consent=False,chat_messages=[],chat_draft='Unsent',
            chat_input=Mock(),client=Mock(return_value=Mock()),run_job=Mock(),show_result=Mock(),
            after=Mock(),restore_chat_input=Mock(),render_chat=Mock(),status=Mock())

    def test_chat_refusal_preserves_draft_and_does_not_call_provider(self):
        fake=self.fake();fake.chat_input.get.return_value='Question'
        with patch('community.app.messagebox.askyesno',return_value=False):
            CommunityApp.send_chat(fake)
        fake.run_job.assert_not_called();fake.chat_input.delete.assert_not_called()
        self.assertFalse(fake.chat_consent)

    def test_chat_success_updates_history_only_after_response(self):
        fake=self.fake();fake.chat_input.get.return_value='Question'
        with patch('community.app.messagebox.askyesno',return_value=True):
            CommunityApp.send_chat(fake)
        self.assertEqual(fake.chat_messages,[])
        work,done,_=fake.run_job.call_args.args
        fake.client.return_value.complete.return_value='Answer'
        self.assertEqual(work(),'Answer')
        done('Answer')
        self.assertEqual([x['content'] for x in fake.chat_messages],['Question','Answer'])
        self.assertEqual(fake.chat_draft,'')
        fake.chat_input.delete.assert_called_once()

    def test_chat_retry_restores_editor_without_clearing_draft(self):
        fake=self.fake();fake.page='Chat'
        CommunityApp.restore_chat_input(fake)
        fake.chat_input.configure.assert_called_with(state='normal')
        fake.chat_input.delete.assert_not_called()

    def test_model_update_rolls_back_when_config_save_fails(self):
        fake=self.fake()
        fake.key_var=Mock();fake.key_var.get.return_value='test-key'
        fake.model_var=Mock();fake.model_var.get.return_value='new-model'
        fake.persist_var=Mock();fake.persist_var.get.return_value=False
        fake.settings=SimpleNamespace(model='old-model',save=Mock(side_effect=ConfigurationError('Cannot save')),
            get_api_key=Mock(return_value=''),set_api_key=Mock())
        fake.navigate=Mock()
        with patch('community.app.create_client',return_value=Mock()):
            CommunityApp.connect_ai(fake)
        work,done,_=fake.run_job.call_args.args
        done(True)
        self.assertEqual(fake.settings.model,'old-model')
        fake.settings.set_api_key.assert_not_called()
        fake.show_result.assert_called_once()
