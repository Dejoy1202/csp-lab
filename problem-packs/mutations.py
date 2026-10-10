"""Ensure generated formal points reject selected, known wrong C++ programs."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import uuid
from sandbox import Sandbox
from checkers import check_output
from validation_runtime import ValidationRuntime

ROOT=Path(__file__).resolve().parent

def verify_mutations(batch, problems, sandbox, positions=None):
    definitions=json.loads((ROOT/batch/'mutations.json').read_text(encoding='utf-8'))
    assert {m['position'] for m in definitions}==set(range(1,6)), 'Every paper problem needs a wrong-program regression'
    assert len({(m['position'],m['name']) for m in definitions})==len(definitions), 'Duplicate mutant definition'
    positions=set(range(1,6)) if positions is None else set(positions)
    assert positions and positions<=set(range(1,6)), 'Invalid problem positions'
    evidence=[]
    for mutant in definitions:
        if mutant['position'] not in positions:continue
        problem=problems[mutant['position']-1]
        source_path=(ROOT/batch/mutant.get('sourceFile',f"reference/{mutant['position']}.cpp")).resolve()
        assert source_path.is_relative_to((ROOT/batch).resolve()), 'Mutant source must stay inside its paper folder'
        source=source_path.read_text(encoding='utf-8')
        for before,after in mutant.get('edits',[]):
            assert source.count(before)==1, f"Ambiguous mutation: {mutant['name']}: {before}"
            source=source.replace(before,after,1)
        binary,diagnostic=sandbox.compile(source)
        assert binary is not None, f"Mutant must compile: {mutant['name']}: {diagnostic}"
        witness=None
        with ValidationRuntime(sandbox,binary,problem['timeLimitMs'],problem['memoryLimitMb'],problem.get('outputLimitKb',1024)) as runtime:
            for ordinal,case in enumerate(problem['testCases'],1):
                result=runtime.run(case['input'])
                if result['status']!='OK' or not check_output(case.get('checkerType','TOKENS'),case['input'],case['output'],result['stdout'].encode()):
                    witness=dict(problem=problem['code'],mutant=mutant['name'],reason=mutant['reason'],
                        rejectedAtTestPoint=ordinal,status='WA' if result['status']=='OK' else result['status'],
                        inputSha256=hashlib.sha256(case['input'].encode()).hexdigest(),
                        sourceSha256=hashlib.sha256(source.encode()).hexdigest())
                    break
        assert witness is not None, f"Formal dataset failed to detect {mutant['name']}"
        evidence.append(witness)
        print(f"Mutation {problem['code']} {mutant['name']}: detected at point {witness['rejectedAtTestPoint']}",flush=True)
    return dict(batch=batch,status='PASS',positions=sorted(positions),allSelectedMutantsRejected=True,mutants=evidence,
        limitation='Selected defect witnesses; not proof of exhaustive error detection')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True);parser.add_argument('--output',default='/output');args=parser.parse_args()
    assert len(args.batch)==6 and args.batch.isdigit()
    out=Path(args.output)
    problems=[json.loads(gzip.decompress((out/f'{args.batch}-{i}.json.gz').read_bytes()))['problems'][0] for i in range(1,6)]
    sandbox=Sandbox(os.environ.get('SANDBOX_IMAGE','csp-lab-sandbox:local'),'mutation-'+uuid.uuid4().hex)
    report=verify_mutations(args.batch,problems,sandbox)
    (out/f'{args.batch}-mutations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
