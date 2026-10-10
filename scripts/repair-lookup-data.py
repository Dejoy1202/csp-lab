"""Rebuild only CSP43 T1, then publish through the versioned admin API."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'worker'),str(ROOT/'problem-packs')]
from sandbox import Sandbox, tokens
from validation_runtime import ValidationRuntime
from mutations import verify_mutations

def main(publish):
    folder=ROOT/'problem-packs/202609'
    output=ROOT/'problem-packs/generated'
    spec=importlib.util.spec_from_file_location('lookup_data',folder/'data.py')
    data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
    path=output/'202609-1.json.gz'
    old=path.read_bytes()
    problem=json.loads(gzip.decompress(old))['problems'][0]
    source=(folder/'reference/1.cpp').read_text(encoding='utf-8')
    sandbox=Sandbox(None,'lookup-data-repair')
    binary,diagnostic=sandbox.compile(source)
    assert binary is not None,diagnostic
    formal=list(data.dataset(1));small=list(data.small_cases(1))
    assert len(formal)==20 and sum(data.parse(1,c)[0]==1 for c in formal)==10
    cases=[];evidence=[]
    with ValidationRuntime(sandbox,binary,problem['timeLimitMs'],problem['memoryLimitMb']) as runtime:
        def check(text):
            data.validate(1,text)
            expected=data.oracle(1,text)
            actual=runtime.run(text)
            assert actual['status']=='OK' and tokens(actual['stdout'].encode())==tokens(expected.encode())
            return actual
        for sample in problem['samples']:
            actual=check(sample['input'])
            assert tokens(actual['stdout'].encode())==tokens(sample['output'].encode())
        for text in small:check(text)
        for ordinal,text in enumerate(formal,1):
            actual=check(text)
            cases.append(dict(input=text,output=actual['stdout'],score=5,subtaskKey=None))
            evidence.append(dict(ordinal=ordinal,inputBytes=len(text.encode()),outputBytes=len(actual['stdout'].encode()),
                inputSha256=hashlib.sha256(text.encode()).hexdigest(),outputSha256=hashlib.sha256(actual['stdout'].encode()).hexdigest(),
                referenceTimeMs=actual['time_ms'],referenceMemoryKb=actual['memory_kb']))
    report=json.loads(problem['validationReport'])
    report.update(cases=evidence,smallDifferentialCases=len(small),
        repair='Binary floating midpoint cancellation; CDF table validation',
        boundaryCases=['exact non-binary midpoint','cancellation with tiny positive delta','either side of midpoint','both table endpoints','variance sum of 100 terms'],
        cdfValidation='Independent 80-digit Decimal integration series checks every rounded table value')
    problem['testCases']=cases;problem['validationReport']=json.dumps(report,ensure_ascii=False)
    for asset in problem['assets']:
        if asset['name'] in ('data.py','validator-oracle.py'):asset['content']=(folder/'data.py').read_text(encoding='utf-8')
    problem['scoringNotes']='本站模拟评分；20个自建测试点，每点5分，50%点n=1。已补精确中点浮点消减、两侧邻近值及端点回归；非官方隐藏数据或认证成绩。'
    problems=[problem]+[json.loads(gzip.decompress((output/f'202609-{i}.json.gz').read_bytes()))['problems'][0] for i in range(2,6)]
    # Validate the entire paper's known mutants, including the actual double bug.
    mutations=verify_mutations('202609',problems,sandbox)
    content=gzip.compress(json.dumps({'problems':[problem]},ensure_ascii=False).encode(),mtime=0)
    backup=ROOT/'backups'/('202609-1-before-precision-'+time.strftime('%Y%m%d-%H%M%S')+'.json.gz')
    backup.parent.mkdir(exist_ok=True);backup.write_bytes(old)
    path.write_bytes(content)
    reports=json.loads((output/'202609-validation.json').read_text(encoding='utf-8'))
    reports[0]=report
    (output/'202609-validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'202609-mutations.json').write_text(json.dumps(mutations,ensure_ascii=False,indent=2),encoding='utf-8')
    receipt=dict(status='PASS',formalPoints=20,smallChecks=len(small),samples=len(problem['samples']),
        oldInputHashes=[hashlib.sha256(c['input'].encode()).hexdigest() for c in json.loads(gzip.decompress(old))['problems'][0]['testCases']],
        newInputHashes=[c['inputSha256'] for c in evidence],mutants=mutations['mutants'],historicalSubmissionsModified=False)
    if publish:
        base=os.environ.get('BASE_URL','http://127.0.0.1:8080')
        headers={'X-API-Key':os.environ['API_KEY'],'Content-Type':'application/json'}
        request=urllib.request.Request(base+'/api/problems?batch=202609&size=100',headers=headers)
        with urllib.request.urlopen(request,timeout=30) as response:items=json.load(response)['items']
        identifier=next(p['id'] for p in items if p['code']=='202609-1')
        request=urllib.request.Request(base+f'/api/admin/problems/{identifier}',data=json.dumps(problem,ensure_ascii=False).encode(),headers=headers,method='PUT')
        # The backend refuses edits during active exams or queued/running submissions.
        with urllib.request.urlopen(request,timeout=60) as response:json.load(response)
        receipt['databasePublished']=True
    else:receipt['databasePublished']=False
    target=ROOT/'docs/validation/lookup-precision-repair.json'
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: 20 formal points, {len(small)} independent checks, {len(mutations["mutants"])} rejected mutants; database published={publish}',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true')
    main(parser.parse_args().publish)
