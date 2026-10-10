"""Compile and sample-run all imported references in real Windows sandboxes."""
import concurrent.futures
import argparse
import gzip
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'worker'))
from sandbox import Sandbox
from checkers import check_output
FORMAL=False

def check(path):
    problem=json.loads(gzip.decompress(path.read_bytes()))['problems'][0]
    code=problem['code'];batch,position=code.split('-')
    source=(ROOT/f'problem-packs/{batch}/reference/{position}.cpp').read_text(encoding='utf-8')
    sandbox=Sandbox(None,'reference-compatibility')
    binary,diagnostic=sandbox.compile(source)
    assert binary is not None,f'{code} compile failed: {diagnostic[:2000]}'
    for sample in problem['samples']:
        report=sandbox.run(binary,sample['input'],problem['timeLimitMs'],problem['memoryLimitMb'],problem.get('outputLimitKb',1024))
        assert report['status']=='OK',f'{code}: {report["status"]}'
        assert check_output(sample.get('checkerType','TOKENS'),sample['input'],sample['output'],report['stdout'].encode()),f'{code}: sample output mismatch'
    if FORMAL:
        for ordinal,case in enumerate(problem['testCases'],1):
            report=sandbox.run(binary,case['input'],problem['timeLimitMs'],problem['memoryLimitMb'],problem.get('outputLimitKb',1024))
            assert report['status']=='OK',f'{code} formal point {ordinal}: {report["status"]}'
            assert check_output(case.get('checkerType','TOKENS'),case['input'],case['output'],report['stdout'].encode()),f'{code} formal point {ordinal}: output mismatch'
    count=len(problem['testCases']) if FORMAL else 0
    print(f'{code}: Windows C++17 / {len(problem["samples"])} sample(s) / {count} formal point(s) PASS',flush=True)
    return {'problem':code,'status':'PASS','samples':len(problem['samples']),'formalPoints':count}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--formal',action='store_true');parser.add_argument('--workers',type=int,default=1);parser.add_argument('--from-problem');args=parser.parse_args();FORMAL=args.formal
    paths=sorted((ROOT/'problem-packs/generated').glob('??????-?.json.gz'))
    assert len(paths)==50,'Expected ten complete five-question packs'
    if args.from_problem:paths=[path for path in paths if path.name.split('.')[0]>=args.from_problem]
    # The production worker judges serially; timing checks use the same load.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        evidence=list(executor.map(check,paths))
    name='reference-formal-remaining.json' if args.from_problem else 'reference-formal.json' if FORMAL else 'reference-compatibility.json'
    target=ROOT/'test-results/windows'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'status':'PASS','sandbox':'Windows AppContainer + Job Object','problems':len(paths),'formalPoints':sum(row['formalPoints'] for row in evidence),'limitation':'Reference compatibility on authored data, not proof of detecting every incorrect program','evidence':evidence},ensure_ascii=False,indent=2),encoding='utf-8')
