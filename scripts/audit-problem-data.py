"""Audit authored packs: input contracts, provenance, small answers and mutants.

Passing this audit is not a proof that every incorrect program is rejected.
Large answers are not regenerated here; their existing certificates are retained.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
PACKS=ROOT/'problem-packs'
sys.path[:0]=[str(ROOT/'worker'),str(PACKS)]
from checkers import TYPES,check_output
from sandbox import Sandbox
from mutations import verify_mutations

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def audit(refresh,refresh_batches=()):
    evidence=[];issues=[];mutants=[]
    paths=sorted((PACKS/'generated').glob('??????-?.json.gz'))
    assert len(paths)==50,'Expected 50 completed authored packs'
    batches=sorted({path.name[:6] for path in paths})
    requested=set(batches) if refresh else set(refresh_batches)
    assert requested<=set(batches),'Unknown mutation refresh batch'
    for batch in batches:
        folder=PACKS/batch
        module=load(folder/('validators.py' if batch=='202403' else 'data.py'),'audit_'+batch)
        oracle_module=load(folder/'oracles.py','audit_oracles_'+batch) if batch=='202403' else module
        problems=[]
        for position in range(1,6):
            problem=json.loads(gzip.decompress((PACKS/f'generated/{batch}-{position}.json.gz').read_bytes()))['problems'][0]
            problems.append(problem);code=problem['code']
            checks=problem['testCases'];groups=problem['subtasks'];report=json.loads(problem['validationReport'])
            assert code==f'{batch}-{position}' and problem['constructionStatus']=='VERIFIED'
            assert sum(c['score'] for c in checks)+sum(g['score'] for g in groups)==100
            group_keys={g['key'] for g in groups}
            assert len(group_keys)==len(groups)
            assert all(any(c['subtaskKey']==key for c in checks) for key in group_keys)
            assert all(c.get('checkerType','TOKENS') in TYPES for c in checks+problem['samples'])
            row=dict(problem=code,formalPoints=len(checks),inputContractsChecked=0,freshOracleChecks=0,
                     largeAnswersNotRegenerated=0,issues=[],recordedAnswersUsedForEncryptedInputValidation=False)
            certificates={c['inputSha256']:c for c in report['cases'] if 'inputSha256' in c}
            for ordinal,case in enumerate(checks,1):
                key=case.get('subtaskKey')
                assert key in group_keys and case['score']==0 if key else case['score']>0
                digest=hashlib.sha256(case['input'].encode()).hexdigest()
                if certificates and digest not in certificates:
                    row['issues'].append(f'point {ordinal}: missing input digest certificate')
                if digest in certificates and certificates[digest].get('outputSha256')!=hashlib.sha256(case['output'].encode()).hexdigest():
                    row['issues'].append(f'point {ordinal}: output digest differs from certificate')
            for kind,cases in [('sample',problem['samples']),('formal',checks)]:
                for ordinal,case in enumerate(cases,1):
                    try:
                        # Decoding encrypted large operations needs the pack's
                        # recorded answers. This checks syntax/legal operations,
                        # and is explicitly not a fresh independent answer proof.
                        if batch=='202603' and position==5:
                            n,X,edges,stations,plans,events=module.parse(5,case['input'])
                            if n>100:
                                module.TRAVEL[hashlib.sha256(case['input'].encode()).hexdigest()]=(case['output'],None)
                                row['recordedAnswersUsedForEncryptedInputValidation']=True
                        if batch=='202403':module.validate(position,case['input'],case.get('subtaskKey'))
                        elif batch=='202603' and position==5 and module.parse(5,case['input'])[0]>100:
                            # Avoid the optional original decoded-operation-list
                            # comparison; the full legality checks still execute.
                            digest=hashlib.sha256(case['input'].encode()).hexdigest()
                            n,X,edges,stations,plans,events=module.parse(5,case['input'])
                            last=0;answers=iter(map(int,case['output'].split()));decoded=[]
                            for event in events:
                                if event[0]==2:last=next(answers);decoded.append(event)
                                else:decoded.append((1,event[1]^(X*last),event[2]^(X*last)))
                            module.TRAVEL[digest]=(case['output'],decoded)
                            module.validate(position,case['input'])
                        else:module.validate(position,case['input'])
                        row['inputContractsChecked']+=1
                        if len(case['input'].encode())>8192:
                            row['largeAnswersNotRegenerated']+=1;continue
                        oracle=getattr(oracle_module,['one','two','three','four','five'][position-1]) if batch=='202403' else lambda text:module.oracle(position,text)
                        expected=oracle(case['input'])
                        assert check_output(case.get('checkerType','TOKENS'),case['input'],expected,case['output'].encode()),'Independent answer mismatch'
                        row['freshOracleChecks']+=1
                    except Exception as error:
                        row['issues'].append(f'{kind} {ordinal}: {type(error).__name__}: {error}')
            definition=folder/'mutations.json'
            names=[] if not definition.exists() else [m['name'] for m in json.loads(definition.read_text(encoding='utf-8')) if m['position']==position]
            row['selectedWrongPrograms']=names
            if not names:row['issues'].append('No selected wrong-program regressions')
            evidence.append(row)
            issues.extend(dict(problem=code,detail=issue) for issue in row['issues'])
            print(f'{code}: {row["inputContractsChecked"]} inputs, {row["freshOracleChecks"]} fresh answers, {len(names)} mutants, {len(row["issues"])} issues',flush=True)
        target=PACKS/f'generated/{batch}-mutations.json'
        if batch in requested:
            current=verify_mutations(batch,problems,Sandbox(None,'data-audit-'+batch))
            target.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
        if target.exists():
            current=json.loads(target.read_text(encoding='utf-8'))
            assert current['status']=='PASS'
            actual={(m['problem'],m['mutant']) for m in current['mutants']}
            expected={(f'{batch}-{m["position"]}',m['name']) for m in json.loads((folder/'mutations.json').read_text(encoding='utf-8'))}
            if actual!=expected:issues.append(dict(problem=batch,detail='Mutant evidence does not match current definitions'))
            mutants.extend(current['mutants'])
        else:issues.append(dict(problem=batch,detail='No mutation verification artifact'))
    receipt=dict(status='PASS' if not issues else 'NEEDS_ATTENTION',checkedAt=datetime.now(timezone.utc).isoformat(),
        problems=len(evidence),formalPoints=sum(r['formalPoints'] for r in evidence),
        inputContractsChecked=sum(r['inputContractsChecked'] for r in evidence),freshOracleChecks=sum(r['freshOracleChecks'] for r in evidence),
        selectedWrongPrograms=len(mutants),mutantsReexecuted=requested==set(batches),mutantBatchesReexecuted=sorted(requested),issues=issues,evidence=evidence,
        limitation='Finite selected errors only. Large outputs retain prior certificates and are not all freshly regenerated; encrypted large input legality uses recorded answers. No claim of official data equivalence or exhaustive correctness.')
    target=ROOT/'docs/validation/problem-data-audit.json'
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('evidence','limitation')},ensure_ascii=False),flush=True)
    return not issues

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group()
    group.add_argument('--refresh-mutants',action='store_true')
    group.add_argument('--refresh-batches',nargs='+',default=[])
    args=parser.parse_args()
    sys.exit(0 if audit(args.refresh_mutants,args.refresh_batches) else 1)
