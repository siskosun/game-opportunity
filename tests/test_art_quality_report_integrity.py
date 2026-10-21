"""Synthetic-only regression tests for source binding and preflight arithmetic."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.art_quality_pilot import metrics, preflight


class ReportIntegrityTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.records = self.root / 'records.json'
        self.records.write_text(json.dumps({
            'schema_version':'1.0', 'study_id':'SYNTHETIC-SOURCE-PIN',
            'study_kind':'synthetic','required_review_criteria':['identity'],
            'records':[]
        }, ensure_ascii=False), encoding='utf-8')

    def _call(self, func, argv):
        output = StringIO()
        with patch.object(sys, 'argv', argv), redirect_stdout(output), \
             patch.object(metrics, 'use_upstream', return_value={'ok':True}):
            code = func()
        return code, json.loads(output.getvalue())

    def test_metrics_binds_exact_input_bytes_and_uses_exclusive_create(self):
        output = self.root / 'metrics.json'
        code, result = self._call(metrics.main, ['metrics.py',str(self.records),'--out',str(output)])
        self.assertEqual(code, 0)
        digest = hashlib.sha256(self.records.read_bytes()).hexdigest()
        self.assertEqual(result['records_sha256'], digest)
        self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['records_sha256'], digest)
        again, err = self._call(metrics.main, ['metrics.py',str(self.records),'--out',str(output)])
        self.assertEqual(again, 2)
        self.assertFalse(err['ok'])
        self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['records_sha256'], digest)

    def test_metrics_rejects_dangling_symlink_report_destination(self):
        output = self.root / 'symlink-metrics.json'
        unseen = self.root / 'unseen' / 'do-not-create.json'
        try:
            output.symlink_to(unseen)
        except (OSError, NotImplementedError):
            self.skipTest('Creating a symlink is not available in this runner')
        code, res = self._call(metrics.main, ['metrics.py',str(self.records),'--out',str(output)])
        self.assertEqual(code, 2)
        self.assertFalse(res['ok'])
        self.assertFalse(unseen.exists())

    def test_preflight_binds_exact_source_bytes_without_claiming_real_baseline(self):
        out = self.root / 'preflight.json'
        code, result = self._call(preflight.main, ['preflight.py',str(self.records),'--root',str(self.root),'--out',str(out)])
        self.assertEqual(code, 1)
        expected = hashlib.sha256(self.records.read_bytes()).hexdigest()
        self.assertEqual(result['records_sha256'], expected)
        self.assertFalse(result['baseline_capture_ready'])
        self.assertFalse(result['production_approved'])
        self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['records_sha256'], expected)

if __name__=='__main__':
    unittest.main()
