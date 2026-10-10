"""Regression tests for refusing papers with missing/surviving wrong programs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'worker'),str(ROOT/'problem-packs')]
import mutations
import early


class FakeSandbox:
    def __init__(self,*args):self.calls=0
    def compile(self,source):
        self.calls+=1
        return source.encode(),''


class WrongRuntime:
    def __init__(self,*args):pass
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def run(self,data):return dict(status='OK',stdout='wrong\n',time_ms=1,memory_kb=1)


class CorrectRuntime(WrongRuntime):
    def run(self,data):return dict(status='OK',stdout='right\n',time_ms=1,memory_kb=1)


class MutationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        folder=self.root/'201312';(folder/'reference').mkdir(parents=True)
        self.problems=[];self.definitions=[]
        for i in range(1,6):
            (folder/f'reference/{i}.cpp').write_text('int main(){return 0;}',encoding='utf-8')
            self.problems.append(dict(code=f'201312-{i}',sourceBatch='201312',sourcePosition=i,
                timeLimitMs=1000,memoryLimitMb=64,samples=[],testCases=[dict(input='1\n',output='right\n',score=100)]))
            self.definitions.append(dict(position=i,name='return-one',reason='selected defect',edits=[['return 0','return 1']]))
        self.write_definitions()
        self.addCleanup(patch.stopall)
        patch.object(mutations,'ROOT',self.root).start()
        patch.object(mutations,'ValidationRuntime',WrongRuntime).start()

    def write_definitions(self):
        (self.root/'201312/mutations.json').write_text(json.dumps(self.definitions),encoding='utf-8')

    def test_complete_paper_rejections(self):
        sandbox=FakeSandbox()
        report=mutations.verify_mutations('201312',self.problems,sandbox)
        self.assertEqual(len(report['mutants']),5)
        self.assertEqual(report['positions'],[1,2,3,4,5])
        self.assertEqual(sandbox.calls,5)

    def test_missing_question_rejected_before_compilation(self):
        self.definitions.pop();self.write_definitions();sandbox=FakeSandbox()
        with self.assertRaisesRegex(AssertionError,'Every paper problem'):
            mutations.verify_mutations('201312',self.problems,sandbox)
        self.assertEqual(sandbox.calls,0)

    def test_partial_rebuild_checks_selected_question(self):
        sandbox=FakeSandbox()
        report=mutations.verify_mutations('201312',self.problems,sandbox,{2})
        self.assertEqual(report['positions'],[2]);self.assertEqual(sandbox.calls,1)
        self.assertEqual(report['mutants'][0]['problem'],'201312-2')

    def test_surviving_wrong_program_blocks_paper(self):
        with patch.object(mutations,'ValidationRuntime',CorrectRuntime):
            with self.assertRaisesRegex(AssertionError,'failed to detect'):
                mutations.verify_mutations('201312',self.problems,FakeSandbox())

    def test_compile_failure_is_not_a_valid_witness(self):
        sandbox=FakeSandbox();sandbox.compile=lambda source:(None,'compile error')
        with self.assertRaisesRegex(AssertionError,'Mutant must compile'):
            mutations.verify_mutations('201312',self.problems,sandbox)

    def test_duplicate_definition_rejected(self):
        self.definitions.append(self.definitions[0]);self.write_definitions()
        with self.assertRaisesRegex(AssertionError,'Duplicate'):
            mutations.verify_mutations('201312',self.problems,FakeSandbox())

    def test_source_cannot_escape_paper_folder(self):
        self.definitions[0]['sourceFile']='../outside.cpp';self.write_definitions()
        with self.assertRaisesRegex(AssertionError,'inside its paper folder'):
            mutations.verify_mutations('201312',self.problems,FakeSandbox())

    def test_failed_gate_preserves_existing_pack_and_database(self):
        folder=self.root/'201312'
        (folder/'statements.json').write_text(json.dumps(self.problems),encoding='utf-8')
        (folder/'data.py').write_text("SEED=1\ndef validate(p,d): pass\ndef oracle(p,d): return 'right\\n'\ndef small_cases(p): return []\ndef dataset(p): return ['1\\n']\n",encoding='utf-8')
        output=self.root/'output';output.mkdir()
        sentinel=output/'201312-1.json.gz';sentinel.write_bytes(b'previous validated pack')
        with patch.object(early,'ROOT',self.root),patch.object(early,'Sandbox',FakeSandbox),patch.object(early,'ValidationRuntime',CorrectRuntime),patch.object(early,'verify_mutations',side_effect=AssertionError('surviving mutant')),patch.object(early,'import_file') as importer:
            with self.assertRaisesRegex(AssertionError,'surviving mutant'):
                early.build('201312',output,True)
            importer.assert_not_called()
        self.assertEqual(sentinel.read_bytes(),b'previous validated pack')
        self.assertEqual(len(list(output.iterdir())),1)


if __name__=='__main__':unittest.main(verbosity=2)
