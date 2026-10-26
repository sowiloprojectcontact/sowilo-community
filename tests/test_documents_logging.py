"""PDF parser diagnostics must not disclose private file bytes."""
import concurrent.futures
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.documents import DocumentError, DocumentsService
from modules.documents.service import _private_pdf_logs


class DocumentsLoggingTests(unittest.TestCase):
    def test_corrupt_pdf_diagnostics_hide_content_and_restore_factory(self):
        import pypdf  # Ensure the optional PDF feature is installed for this test.
        previous = logging.getLogRecordFactory()
        with TemporaryDirectory() as directory:
            source = Path(directory) / 'private.pdf'
            source.write_bytes(b'SECRET_PRIVATE_CONTENT no PDF body')
            service = DocumentsService([directory])
            with self.assertLogs('pypdf', level='WARNING') as captured:
                with self.assertRaises(DocumentError) as raised:
                    service.read(source)
            self.assertEqual(raised.exception.code, 'read_error')
            diagnostics = '\n'.join(captured.output)
            self.assertNotIn('SECRE', diagnostics)
            self.assertNotIn('SECRET_PRIVATE_CONTENT', diagnostics)
            self.assertIn('Diagnostic PDF masqué', diagnostics)
        self.assertIs(logging.getLogRecordFactory(), previous)

    def test_guard_preserves_other_thread_and_unrelated_logger(self):
        previous = logging.getLogRecordFactory()
        with self.assertLogs(level='WARNING') as captured:
            with _private_pdf_logs():
                logging.getLogger('pypdf._reader').warning('PRIVATE_BYTES')
                logging.getLogger('sowilo').warning('ordinary diagnostic')
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(logging.getLogger('pypdf._reader').warning,
                                'other thread diagnostic').result()
        logs = '\n'.join(captured.output)
        self.assertNotIn('PRIVATE_BYTES', logs)
        self.assertIn('ordinary diagnostic', logs)
        self.assertIn('other thread diagnostic', logs)
        self.assertIs(logging.getLogRecordFactory(), previous)
