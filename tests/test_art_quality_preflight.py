"""Only synthetic scenarios: no actual art provenance or reviewer approvals."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.art_quality_pilot import evidence, preflight, metrics


class RealBaselinePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'assets').mkdir()
        self.asset=self.root/'assets'/'sample.png'
        self.asset.write_bytes(b'PILOT TEST DATA; NOT A VALID PRODUCTION IMAGE')
        self.rec={
            'id':'mock-a','task_id':'mock-task-1','cohort':'ai_proxy','condition':'A',
            'participant_id':'mock-agent','execution_status':'completed',
            'attempts':[{'attempt':1,'artifact_path':'assets/sample.png',
                         'artifact_sha256':evidence.digest(self.asset),
                         'tool':'mock-tool','model':'mock-model',
                         'elapsed_minutes':5,'cost':1.0,'currency':'USD',
                         'review':{'identity':'unknown'}}],
            'manual_work_minutes':12,'review_minutes':3,
            'final_quality':{'status':'unknown'}
        }
        self.records={'schema_version':'1.0','study_id':'MOCK-NOT-REAL',
                      'study_kind':'synthetic','required_review_criteria':['identity'],
                      'records':[self.rec]}
        # Mock only the upstream schema reader, not the provenance verifier;
        # real upstream integration is covered by CI's vendored pilot tests.
        self.patch=patch.object(metrics,'use_upstream',return_value={'ok':True})
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_synthetic_marked_not_ready(self):
        output=preflight.assess(self.records,self.root)
        self.assertTrue(output['ok'])
        self.assertFalse(output['baseline_capture_ready'])
        self.assertEqual(output['artifact_verified_records'],1)
        self.assertFalse(output['production_approved'])
        self.assertTrue(any('synthetic' in w for w in output['warnings']))

    def test_mock_real_never_claims_human_approval(self):
        self.records['study_kind']='real'
        output=preflight.assess(self.records,self.root)
        self.assertTrue(output['file_intake_ready'])
        self.assertFalse(output['baseline_capture_ready'])  # review provenance missing
        self.assertFalse(output['paired_comparison_ready'])
        self.assertFalse(output['production_approved'])
        self.assertIn('independent review',output['scope'])

    def test_pairs_require_both_conditions_same_task(self):
        self.records['study_kind']='real'
        b=copy.deepcopy(self.rec)
        b.update(id='mock-b',condition='B')
        self.records['records'].append(b)
        output=preflight.assess(self.records,self.root)
        self.assertFalse(output['paired_comparison_ready']) # missing review receipts
        self.assertEqual(output['paired_task_count'],1)
        self.assertEqual(output['time_observed_records'],2)
        b['task_id']='different-task'
        self.assertEqual(preflight.assess(self.records,self.root)['paired_task_count'],0)

    def test_review_receipts_allow_ready_for_independent_review_only(self):
        self.records['study_kind']='real'
        file=self.root/'review.txt'
        file.write_text('Mock verdict with no genuine human authorization', encoding='utf-8')
        self.rec['final_quality']={'status':'reviewed','defects':[]}
        self.rec['final_review_evidence']={'path':'review.txt','sha256':evidence.digest(file)}
        out=preflight.assess(self.records,self.root)
        self.assertTrue(out['baseline_capture_ready'],out)
        self.assertFalse(out['production_approved'])
        self.assertEqual(out['documented_final_review_files'],1)
        b=copy.deepcopy(self.rec)
        b['id']='mock-b'
        b['condition']='B'
        self.records['records'].append(b)
        matched=preflight.assess(self.records,self.root)
        self.assertTrue(matched['paired_comparison_ready'])
        self.assertFalse(matched['production_approved'])
        file.write_text('different reviewer contents',encoding='utf-8')
        changed=preflight.assess(self.records,self.root)
        self.assertFalse(changed['baseline_capture_ready'])
        self.assertIn('sha256 mismatch',json.dumps(changed['file_errors']))

    def test_tampering_and_traversal_are_reported(self):
        self.records['study_kind']='real'
        self.asset.write_bytes(b'changed')
        output=preflight.assess(self.records,self.root)
        self.assertFalse(output['ok'])
        self.assertFalse(output['baseline_capture_ready'])
        self.assertTrue(any('sha256 mismatch' in e for e in output['file_errors']))
        self.records['records'][0]['attempts'][0]['artifact_path']='../unsafe.png'
        self.assertTrue(preflight.assess(self.records,self.root)['file_errors'])

    def test_missing_artifact_does_not_become_zero_defect(self):
        self.records['study_kind']='real'
        self.records['records'][0]['attempts'][0]['artifact_path']=None
        out=preflight.assess(self.records,self.root)
        self.assertFalse(out['baseline_capture_ready'])
        self.assertFalse(out['production_approved'])
        self.assertIn('without artifact',json.dumps(out))

    def test_failed_tool_call_can_have_no_image(self):
        self.records['study_kind']='real'
        rec=self.records['records'][0]
        rec['execution_status']='failed'
        rec['attempts'][0]['artifact_path']=None
        rec['attempts'][0]['review']={}
        out=preflight.assess(self.records,self.root)
        self.assertTrue(out['ok'],out['file_errors'])
        self.assertFalse(out['baseline_capture_ready'])
        self.assertEqual(out['attempted_records'],1)

    def test_real_mock_with_missing_cost_and_human_marks_warning(self):
        self.records['study_kind']='real'
        self.rec['attempts'][0]['cost']=None
        self.rec['review_minutes']=None
        self.rec['final_quality']={'status':'reviewed','defects':[]}
        out=preflight.assess(self.records,self.root)
        self.assertTrue(any('elapsed time or generation cost unobserved' in w for w in out['warnings']))
        self.assertTrue(any('independent review source' in w for w in out['warnings']))
        self.assertEqual(out['time_observed_records'],0)


if __name__=='__main__': unittest.main()

class UpstreamCliIntegrationTest(unittest.TestCase):
    def test_synthetic_cli_never_reports_real_baseline(self):
        import subprocess
        import sys
        repo=Path(__file__).resolve().parents[1]
        if not (repo/'tools/art_quality_pilot/vendor/pilot.py').is_file():
            self.skipTest('Vendored Art Director pilot is present in GitHub CI')
        cmd=[sys.executable,'-m','tools.art_quality_pilot.preflight',
             str(repo/'tools/art_quality_pilot/fixtures/synthetic_records.json'),
             '--root',str(repo)]
        res=subprocess.run(cmd,cwd=repo,capture_output=True,text=True)
        self.assertEqual(res.returncode,1,res.stdout+res.stderr)
        data=json.loads(res.stdout)
        self.assertEqual(data['study_kind'],'synthetic')
        self.assertFalse(data['baseline_capture_ready'])
        self.assertFalse(data['production_approved'])
