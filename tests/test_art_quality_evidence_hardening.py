"""Independent malformed-input and rule-scope tests for P0 evidence binding."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.art_quality_pilot import evidence


class EvidenceHardeningTests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root=Path(td.name)
        (root/'data').mkdir()
        self.root=root
        self.asset=root/'data'/'a.png'
        self.asset.write_bytes(b'NOT AN ACTUAL IMAGE - SYNTHETIC BINDING TEST')
        self.report=root/'data'/'report.json'
        self.report.write_text(json.dumps({
            'command':'check-image','source_path':str(self.asset),
            'sha256':evidence.digest(self.asset),'ok':True,
            'checks':{'width':{'result':'pass'},'height':{'result':'pass'}}
        }),encoding='utf-8')
        self.command=root/'data'/'cmd.txt'
        self.command.write_text('SYNTHETIC cmd, not executed',encoding='utf-8')
        self.brief={
            'pack':{'id':'mock','version':'0.1.0','fingerprint':'f'*64},
            'rules':[{'id':'TECH-1','verification':'technical'}],
            'direction_checks':[{'criterion':'rule/TECH-1','result':'unknown'}]
        }
        self.brief_path=root/'brief.json'
        self.e={
            'schema_version':'art-evidence-v0.1',
            'pack':{'project_id':'mock','version':'0.1.0','fingerprint':'f'*64},
            'asset':{'path':'data/a.png','sha256':evidence.digest(self.asset)},
            'criterion_id':'rule/TECH-1','method':'technical-tool','result':'pass',
            'tool':{'name':'art-director/pilot.py','version':'1.0'},
            'execution':{'command_or_prompt_ref':'data/cmd.txt','command_or_prompt_sha256':evidence.digest(self.command),
                         'raw_output_path':'data/report.json','raw_output_sha256':evidence.digest(self.report)}
        }
        self._refresh_brief()

    def _refresh_brief(self):
        self.brief_path.write_text(json.dumps(self.brief),encoding='utf-8')
        self.e['brief_sha256']=evidence.digest(self.brief_path)

    def check(self,rec=None):
        return evidence.check_record(rec if rec is not None else self.e,root=self.root,
                                     brief=self.brief,brief_sha256=evidence.digest(self.brief_path))

    def test_technical_result_is_binding_only(self):
        result=self.check()
        self.assertTrue(result['ok'],result['errors'])
        self.assertFalse(result['approval'])
        self.assertEqual(result['criterion_assessment'],'not_performed')

    def test_visual_rule_rejects_pixel_pass_even_when_json_consistent(self):
        self.brief['rules'][0]['verification']='visual'
        self._refresh_brief()
        output=self.check()
        self.assertFalse(output['ok'])
        self.assertIn('technical result cannot evaluate',json.dumps(output['errors']))

    def test_unknown_reference_acceptance_rejects_pixel_pass(self):
        self.brief['direction_checks']=[{'criterion':'exemplar/demo/acceptance/1'}]
        self._refresh_brief()
        self.e['criterion_id']='exemplar/demo/acceptance/1'
        self.assertFalse(self.check()['ok'])

    def test_malformed_criterion_and_method_do_not_throw(self):
        self.brief['direction_checks'].append({'criterion':['not-hashable']})
        self._refresh_brief()
        self.e['method']={'unexpected':'object'}
        res=self.check()
        self.assertFalse(res['ok'])
        self.assertIn('method/result: unsupported',res['errors'])

    def test_non_object_json_is_reported_invalid(self):
        self.report.write_text('[]',encoding='utf-8')
        self.e['execution']['raw_output_sha256']=evidence.digest(self.report)
        self.assertFalse(self.check()['ok'])
        self.assertIn('JSON object',json.dumps(self.check()['errors']))

    def test_old_or_replaced_artifact_fails_hash_link(self):
        self.asset.write_bytes(b'DIFFERENT CONTENT')
        out=self.check()
        self.assertFalse(out['ok'])
        self.assertIn('asset: sha256 mismatch',out['errors'])

    def test_vlm_suspected_is_never_approval(self):
        self.e['method']='vlm-triage'
        self.e['result']='suspected'
        self.assertTrue(self.check()['ok'])
        self.assertFalse(self.check()['approval'])


if __name__=='__main__': unittest.main()
