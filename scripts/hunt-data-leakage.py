"""Try new plausible wrong programs against formal data, then find valid escapes.

An escape is confirmed only when the repository reference agrees with an
independent oracle on an input the wrong program fails. No database writes.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
PACKS=ROOT/'problem-packs'
sys.path[:0]=[str(ROOT/'worker'),str(PACKS)]
from sandbox import Sandbox
from checkers import check_output
from validation_runtime import ValidationRuntime


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module


def run(batch_filter,resume):
    definitions=json.loads((PACKS/'leakage-probes.json').read_text(encoding='utf-8'))
    if batch_filter:definitions=[d for d in definitions if d['batch']==batch_filter]
    assert definitions
    suffix='-'+batch_filter if batch_filter else ''
    target=ROOT/f'docs/validation/leakage-hunt{suffix}.json'
    previous=json.loads(target.read_text(encoding='utf-8'))['probes'] if resume and target.exists() else []
    records=[];modules={};problems={};references={}
    sb=Sandbox(None,'leakage-hunt')
    def save():
        report=dict(checkedAt=datetime.now(timezone.utc).isoformat(),status='RUNNING',
                    completed=len(records),planned=len(definitions),
                    missedWrongPrograms=sum(r['status']=='LEAK_CONFIRMED' for r in records),probes=records,
                    limitation='Finite plausible wrong-program probes, not exhaustive proof. A surviving program without an independently verified counterexample is unresolved, not classified as a leak.')
        if len(records)==len(definitions):
            report['status']='NEEDS_REPAIR' if report['missedWrongPrograms'] else 'PASS_FOR_SELECTED_PROBES'
            if any(r['status'] in ('COMPILE_ERROR','UNRESOLVED') for r in records):report['status']='NEEDS_REVIEW'
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for definition in definitions:
        batch=definition['batch'];position=definition['position'];code=f'{batch}-{position}'
        pack=PACKS/f'generated/{code}.json.gz';pack_hash=hashlib.sha256(pack.read_bytes()).hexdigest()
        if code not in problems:problems[code]=json.loads(gzip.decompress(pack.read_bytes()))['problems'][0]
        p=problems[code]
        source=(PACKS/batch/f'reference/{position}.cpp').read_text(encoding='utf-8')
        for before,after in definition['edits']:
            assert source.count(before)==1,f'{code} {definition["name"]}: ambiguous edit {before}'
            source=source.replace(before,after,1)
        source_hash=hashlib.sha256(source.encode()).hexdigest()
        old=next((r for r in previous if r['problem']==code and r['name']==definition['name'] and r['packSha256']==pack_hash and r['sourceSha256']==source_hash and r['status'] not in ('UNRESOLVED','COMPILE_ERROR')),None)
        if old:records.append(old);save();continue
        print(f'{code} {definition["name"]}: testing existing formal points',flush=True)
        binary,diagnostic=sb.compile(source)
        row=dict(problem=code,name=definition['name'],reason=definition['reason'],sourceSha256=source_hash,packSha256=pack_hash,status='UNRESOLVED',existingChecks=0)
        if binary is None:
            row.update(status='COMPILE_ERROR',diagnostic=diagnostic[:500]);records.append(row);save();continue
        with ValidationRuntime(sb,binary,p['timeLimitMs'],p['memoryLimitMb'],p.get('outputLimitKb',1024)) as runtime:
            cache={}
            for ordinal,case in enumerate(p['testCases'],1):
                digest=hashlib.sha256(case['input'].encode()).hexdigest()
                result=cache.get(digest)
                if result is None:result=runtime.run(case['input']);cache[digest]=result
                row['existingChecks']+=1
                if result['status']!='OK' or not check_output(case.get('checkerType','TOKENS'),case['input'],case['output'],result['stdout'].encode()):
                    row.update(status='REJECTED_BY_EXISTING',rejectedAtTestPoint=ordinal,inputSha256=digest)
                    break
            if row['status']=='UNRESOLVED':
                print(f'{code} {definition["name"]}: survives ALL formal checks; searching independent counterexamples',flush=True)
                if batch not in modules:
                    if batch=='202403':
                        modules[batch]=(load(PACKS/batch/'validators.py','hunt_v_'+batch),load(PACKS/batch/'oracles.py','hunt_o_'+batch),load(PACKS/batch/'generator.py','hunt_g_'+batch))
                    else:
                        module=load(PACKS/batch/'data.py','hunt_'+batch);modules[batch]=(module,module,module)
                validator,oracle,generator=modules[batch]
                inputs=list(definition.get('probeCases',[]))
                original_seed=generator.SEED
                try:
                    for offset in (1000003,2000003):
                        generator.SEED=original_seed+offset
                        inputs.extend(generator.small_cases(position))
                finally:generator.SEED=original_seed
                row['searchedInputs']=0
                for text in inputs:
                    validator.validate(position,text)
                    expected=oracle.ORACLES[position](text) if batch=='202403' else oracle.oracle(position,text)
                    row['searchedInputs']+=1
                    result=runtime.run(text)
                    # Grouping needs full semantic validation instead of one
                    # particular optimal partition's literal output.
                    checker='CSP_GROUP_PARTITION' if batch=='202609' and position==4 else p['testCases'][0].get('checkerType','TOKENS')
                    if result['status']=='OK' and check_output(checker,text,expected,result['stdout'].encode()):continue
                    if code not in references:
                        reference,diagnostic=sb.compile((PACKS/batch/f'reference/{position}.cpp').read_text(encoding='utf-8'))
                        assert reference is not None,diagnostic
                        references[code]=reference
                    with ValidationRuntime(sb,references[code],p['timeLimitMs'],p['memoryLimitMb'],p.get('outputLimitKb',1024)) as correct:
                        answer=correct.run(text)
                    assert answer['status']=='OK' and check_output(checker,text,expected,answer['stdout'].encode()),f'{code}: reference/oracle discrepancy'
                    witness=ROOT/f'.runtime/leakage-witnesses/{code}-{definition["name"]}.json'
                    witness.parent.mkdir(parents=True,exist_ok=True)
                    witness.write_text(json.dumps(dict(problem=code,input=text,output=answer['stdout'],oracleOutput=expected,checkerType=checker,source=source),ensure_ascii=False,indent=2),encoding='utf-8')
                    row.update(status='LEAK_CONFIRMED',witness=str(witness.relative_to(ROOT)),inputSha256=hashlib.sha256(text.encode()).hexdigest(),wrongVerdict=result['status'] if result['status']!='OK' else 'WA')
                    break
        records.append(row);save()
        print(f'{code} {definition["name"]}: {row["status"]}',flush=True)
    print(f'Completed {len(records)} probes; confirmed leaks: {sum(r["status"]=="LEAK_CONFIRMED" for r in records)}',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batch');parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();run(args.batch,args.resume)
