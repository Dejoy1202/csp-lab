"""Repair confirmed escapes while retaining every previous formal test input."""
import argparse
from datetime import datetime,timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1];PACKS=ROOT/'problem-packs'
sys.path[:0]=[str(ROOT/'worker'),str(PACKS)]
from sandbox import Sandbox
from checkers import check_output
from validation_runtime import ValidationRuntime
from mutations import verify_mutations


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def publish_existing():
    target=ROOT/'docs/validation/leakage-repair.json'
    receipt=json.loads(target.read_text(encoding='utf-8'));assert receipt['status']=='VERIFIED'
    base=os.environ.get('BASE_URL','http://127.0.0.1:8080');headers={'X-API-Key':os.environ['API_KEY'],'Content-Type':'application/json'}
    receipt['published']=[]
    for row in receipt['problems']:
        p=json.loads(gzip.decompress((PACKS/f'generated/{row["problem"]}.json.gz').read_bytes()))['problems'][0]
        certificates={c['inputSha256']:c for c in json.loads(p['validationReport'])['cases']}
        assert len(p['testCases'])==row['formalPoints']
        for case in p['testCases']:
            cert=certificates[hashlib.sha256(case['input'].encode()).hexdigest()]
            assert cert['outputSha256']==hashlib.sha256(case['output'].encode()).hexdigest()
        request=urllib.request.Request(base+f'/api/problems?batch={p["sourceBatch"]}&size=100',headers=headers)
        with urllib.request.urlopen(request,timeout=30) as response:items=json.load(response)['items']
        identifier=next(r['id'] for r in items if r['code']==p['code'])
        detail=urllib.request.Request(base+f'/api/problems/{identifier}',headers=headers)
        with urllib.request.urlopen(detail,timeout=30) as response:current=json.load(response)
        stored_report=current.get('validationReport')
        if isinstance(stored_report,str):stored_report=json.loads(stored_report)
        # MySQL normalizes JSON whitespace/order. Compare the parsed report so
        # retrying publication does not create another identical problem version.
        if stored_report!=json.loads(p['validationReport']):
            request=urllib.request.Request(base+f'/api/admin/problems/{identifier}',data=json.dumps(p,ensure_ascii=False).encode(),headers=headers,method='PUT')
            with urllib.request.urlopen(request,timeout=180) as response:json.load(response)
            with urllib.request.urlopen(detail,timeout=30) as response:current=json.load(response)
        receipt['published'].append(dict(problem=p['code'],id=identifier,version=current['version']))
        target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'Published {p["code"]}, version {current["version"]}',flush=True)
    receipt['databasePublished']=True
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')


def main(publish):
    sb=Sandbox(None,'leakage-repair')
    modules={
        '202403':(load(PACKS/'202403/validators.py','leak_validator'),load(PACKS/'202403/oracles.py','leak_oracle'),load(PACKS/'202403/generator.py','leak_generator')),
        '202609':(load(PACKS/'202609/data.py','leak_data'),)*3,
    }
    completed=[];evidence=[]
    for code in ('202403-3','202609-4','202609-5'):
        batch,position=code.split('-');position=int(position)
        path=PACKS/f'generated/{code}.json.gz'
        original=path.read_bytes();p=json.loads(gzip.decompress(original))['problems'][0]
        old_cases=p['testCases'];validator,oracle,generator=modules[batch]
        if code=='202403-3':
            text=generator.dataset(3)[0][-1][0]
            # Keep the original seven scoring checks unchanged and add one
            # more input to the existing full-domain 40-point subtask.
            p['testCases']=[dict(c) for c in old_cases]+[dict(input=text,output=None,score=0,subtaskKey='s3')]
        elif position==4:
            p['testCases']=[dict(c) for c in old_cases]
            for text in generator.singleton_group_regressions():
                for kind,key in [('CSP_GROUP_COUNT','s1-count'),('CSP_GROUP_PARTITION','s1-plan')]:
                    p['testCases'].append(dict(input=text,output=None,score=0,subtaskKey=key,checkerType=kind))
        else:
            extra=[dict(input=t,output=None,score=0,subtaskKey=None) for t in generator.initial_tree_regressions()]
            p['testCases'],p['subtasks']=generator.configure_scoring(5,[dict(c) for c in old_cases]+extra)
        assert sum(c['score'] for c in p['testCases'])+sum(g['score'] for g in p['subtasks'])==100
        source=(PACKS/batch/f'reference/{position}.cpp').read_text(encoding='utf-8')
        binary,message=sb.compile(source);assert binary is not None,message
        report=json.loads(p['validationReport']);certificates=[];seen={};small_count=0;new_count=0
        def expected(text):
            return oracle.ORACLES[position](text) if batch=='202403' else oracle.oracle(position,text)
        def validate(text,group=None):
            if batch=='202403':validator.validate(position,text,group)
            else:validator.validate(position,text)
        with ValidationRuntime(sb,binary,p['timeLimitMs'],p['memoryLimitMb'],p.get('outputLimitKb',1024)) as runtime:
            for sample in p['samples']:
                validate(sample['input']);answer=expected(sample['input']);result=runtime.run(sample['input'])
                assert result['status']=='OK' and check_output(sample.get('checkerType','TOKENS'),sample['input'],answer,result['stdout'].encode())
            for text in generator.small_cases(position):
                validate(text);answer=expected(text);result=runtime.run(text)
                checker='CSP_GROUP_PARTITION' if position==4 and batch=='202609' else p['testCases'][0].get('checkerType','TOKENS')
                assert result['status']=='OK' and check_output(checker,text,answer,result['stdout'].encode())
                small_count+=1
            for ordinal,case in enumerate(p['testCases'],1):
                validate(case['input'],case.get('subtaskKey'))
                digest=hashlib.sha256(case['input'].encode()).hexdigest()
                if digest not in seen:
                    result=runtime.run(case['input']);assert result['status']=='OK',(code,ordinal,result['status'])
                    if case['output'] is None:
                        answer=expected(case['input'])
                        checker='CSP_GROUP_PARTITION' if batch=='202609' and position==4 else case.get('checkerType','TOKENS')
                        assert check_output(checker,case['input'],answer,result['stdout'].encode()),f'{code}: independent counterexample mismatch'
                        new_count+=1
                    seen[digest]=result
                result=seen[digest]
                if case['output'] is None:case['output']=result['stdout']
                assert check_output(case.get('checkerType','TOKENS'),case['input'],case['output'],result['stdout'].encode()),f'{code}: reference rejected at {ordinal}'
                if not any(c['inputSha256']==digest for c in certificates):
                    certificates.append(dict(ordinal=len(certificates)+1,inputBytes=len(case['input'].encode()),outputBytes=len(case['output'].encode()),
                        inputSha256=digest,outputSha256=hashlib.sha256(case['output'].encode()).hexdigest(),referenceTimeMs=result['time_ms'],referenceMemoryKb=result['memory_kb']))
                print(f'{code}: formal {ordinal}/{len(p["testCases"])} passed',flush=True)
        report.update(cases=certificates,smallDifferentialCases=small_count,
            leakageRepair=dict(checkedAt=datetime.now(timezone.utc).isoformat(),oldFormalPoints=len(old_cases),formalPoints=len(p['testCases']),newIndependentlyVerifiedInputs=new_count,allExistingInputsRetained=True,
                scope='All reference runs refreshed; new/changed inputs and small cases checked by independent oracle. Unchanged large answers retain prior independent certificates.'))
        p['validationReport']=json.dumps(report,ensure_ascii=False)
        for asset in p['assets']:
            if batch=='202403' and asset['name']=='generator.py':asset['content']=(PACKS/batch/'generator.py').read_text(encoding='utf-8')
            if batch=='202609' and asset['name'] in ('data.py','validator-oracle.py'):asset['content']=(PACKS/batch/'data.py').read_text(encoding='utf-8')
        if code=='202609-5':p['scoringNotes']='本站模拟评分：前19个独立点各5分；最后一个原完整规模点与5个初始状态、单节点回归共同组成5分捆绑子任务。保留全部原有输入；非官方隐藏数据或认证成绩。'
        completed.append((path,original,p));evidence.append(dict(problem=code,formalPoints=len(p['testCases']),uniqueInputs=len(certificates),smallChecks=small_count,newIndependentInputs=new_count))
    # Keep all known counterexamples in the paper's mandatory construction gate.
    mutation_reports={}
    for batch in ('202403','202609'):
        problems=[next((p for _,_,p in completed if p['code']==f'{batch}-{i}'),None) or json.loads(gzip.decompress((PACKS/f'generated/{batch}-{i}.json.gz').read_bytes()))['problems'][0] for i in range(1,6)]
        mutation_reports[batch]=verify_mutations(batch,problems,sb)
    backup=ROOT/'backups'/('leakage-repair-'+datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir(parents=True)
    receipt=dict(status='VERIFIED',problems=evidence,historicalSubmissionsModified=False,databasePublished=False)
    for path,original,p in completed:
        (backup/path.name).write_bytes(original)
        path.write_bytes(gzip.compress(json.dumps(dict(problems=[p]),ensure_ascii=False).encode(),mtime=0))
    for batch,report in mutation_reports.items():
        (PACKS/f'generated/{batch}-mutations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        validation_path=PACKS/f'generated/{batch}-validation.json'
        if batch=='202403':validation_path=PACKS/'generated/validation-report.json'
        reports=json.loads(validation_path.read_text(encoding='utf-8'))
        reports=[next((json.loads(p['validationReport']) for _,_,p in completed if p['code']==r['problem']),r) for r in reports]
        validation_path.write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    target=ROOT/'docs/validation/leakage-repair.json'
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    if publish:
        publish_existing()
    print(json.dumps(receipt,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group()
    group.add_argument('--publish',action='store_true');group.add_argument('--publish-existing',action='store_true')
    args=parser.parse_args()
    if args.publish_existing:publish_existing()
    else:main(args.publish)
