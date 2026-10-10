"""Build a whole local CSP paper using the platform's isolated C++ sandbox."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import uuid
from sandbox import Sandbox, tokens
from build import import_file
from validation_runtime import ValidationRuntime
from mutations import verify_mutations

ROOT = Path(__file__).resolve().parent

def build(batch, output, do_import):
    if len(batch) != 6 or not batch.isdigit():
        raise ValueError('Batch must be a six-digit YYYYMM identifier')
    folder = ROOT / batch
    assert (folder/'mutations.json').is_file(), 'A paper needs wrong-program regressions before construction'
    spec = importlib.util.spec_from_file_location('paper_data', folder / 'data.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    problems = json.loads((folder / 'statements.json').read_text(encoding='utf-8'))
    assert len(problems) == 5
    assert [p['sourcePosition'] for p in problems] == list(range(1, 6))
    assert all(p['code'] == f'{batch}-{i}' and p['sourceBatch'] == batch for i,p in enumerate(problems, 1))
    sandbox = Sandbox(os.environ.get('SANDBOX_IMAGE','csp-lab-sandbox:local'), 'paper-' + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=True)
    reports, completed = [], []
    for position, problem in enumerate(problems, 1):
        print(f'{batch} T{position}: compiling inside the isolated sandbox', flush=True)
        source = (folder / f'reference/{position}.cpp').read_text(encoding='utf-8')
        binary, diagnostic = sandbox.compile(source)
        assert binary is not None, diagnostic
        with ValidationRuntime(sandbox,binary,problem['timeLimitMs'],problem['memoryLimitMb'],problem.get('outputLimitKb',1024)) as runtime:
            def check(data):
                module.validate(position, data)
                answer = module.oracle(position, data)
                result = runtime.run(data)
                assert result['status'] == 'OK', f'T{position}: {result}'
                if hasattr(module,'compare'):
                    assert module.compare(position,data,result['stdout'],answer), f'T{position}: differential mismatch'
                else:
                    assert tokens(result['stdout'].encode()) == tokens(answer.encode()), f'T{position}: differential mismatch'
                return result['stdout'], result
            for sample in problem['samples']:
                answer, _ = check(sample['input'])
                if hasattr(module,'compare'):
                    assert module.compare(position,sample['input'],sample['output'],module.oracle(position,sample['input'])), f'T{position}: invalid authored sample'
                else:
                    assert tokens(answer.encode()) == tokens(sample['output'].encode()), f'T{position}: invalid authored sample'
            small = list(module.small_cases(position))
            for data in small:
                check(data)
            print(f'T{position}: samples and {len(small)} differential checks passed', flush=True)
            cases = list(module.dataset(position))
            assert cases and len(cases) <= 100 and (100 % len(cases) == 0 or hasattr(module,'configure_scoring')), 'Independent case scores must sum to 100'
            score = 100 // len(cases) if 100 % len(cases)==0 else 0
            tests, evidence = [], []
            for ordinal, data in enumerate(cases, 1):
                answer, result = check(data)
                tests.append(dict(input=data, output=answer, score=score, subtaskKey=None))
                evidence.append(dict(ordinal=ordinal, inputBytes=len(data.encode()), outputBytes=len(answer.encode()),
                    inputSha256=hashlib.sha256(data.encode()).hexdigest(), outputSha256=hashlib.sha256(answer.encode()).hexdigest(),
                    referenceTimeMs=result['time_ms'], referenceMemoryKb=result['memory_kb']))
                print(f'T{position} case {ordinal}/{len(cases)} passed ({result["time_ms"]} ms)', flush=True)
        report = dict(problem=problem['code'], status='VERIFIED', seed=module.SEED, officialHiddenData=False,
            scoringType='SITE_SIMULATION', answerSource='C++ reference output cross-checked by independent oracle', smallDifferentialCases=len(small), samplesVerified=len(problem['samples']),
            cases=evidence, reference='independent C++17', oracle=getattr(module, 'ORACLE_DESCRIPTION',
                'Python enumeration, combinatorics with brute cross-check, fixed-point reachability'))
        if hasattr(module,'configure_scoring'):
            tests,groups=module.configure_scoring(position,tests)
        else:groups=[]
        assert sum(c['score'] for c in tests)+sum(g['score'] for g in groups)==100, 'Configured scores must total 100'
        extra_assets=module.extra_assets(position) if hasattr(module,'extra_assets') else []
        problem.update(evaluationType='FULL', constructionStatus='VERIFIED',
            license='CSP Lab independently worded specification and generated data; CCF original title/rules attributed; not an official licensed statement copy',
            testCases=tests, subtasks=groups, outputLimitKb=problem.get('outputLimitKb',1024), validationReport=json.dumps(report,ensure_ascii=False),
            assets=[dict(name=f'reference-{position}.cpp',kind='REFERENCE',content=source),
                dict(name='data.py',kind='GENERATOR',content=(folder/'data.py').read_text(encoding='utf-8')),
                dict(name='validator-oracle.py',kind='VALIDATOR',content=(folder/'data.py').read_text(encoding='utf-8'))]+extra_assets)
        content = gzip.compress(json.dumps(dict(problems=[problem]),ensure_ascii=False).encode(),mtime=0)
        completed.append((output / (problem['code'] + '.json.gz'), content))
        reports.append(report)
    mutation_report=verify_mutations(batch,problems,sandbox)
    completed.append((output/(batch+'-mutations.json'),json.dumps(mutation_report,ensure_ascii=False,indent=2).encode('utf-8')))
    # Publish/import only after the whole paper passed. A failure leaves DB unchanged.
    for path, content in completed:
        path.write_bytes(content)
    (output / (batch + '-validation.json')).write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    if do_import:
        for path, _ in completed:
            if not path.name.endswith('.json.gz'): continue
            print(f'Imported {path.name}: {import_file(path)}', flush=True)
    print(f'{batch}: all five independently verified', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch',default='201312')
    parser.add_argument('--output',default='/output')
    parser.add_argument('--import',dest='do_import',action='store_true')
    args = parser.parse_args()
    build(args.batch,Path(args.output),args.do_import)
