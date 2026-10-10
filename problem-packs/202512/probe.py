"""Supplemental reproducible checks for 202512 C/D/E."""
import argparse,itertools,json,random,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import data
from sandbox import Sandbox,tokens
from validation_runtime import ValidationRuntime
def execute(position):
    sandbox=Sandbox('csp-lab-sandbox:local','probe-'+uuid.uuid4().hex)
    binary,error=sandbox.compile((ROOT/f'reference/{position}.cpp').read_text(encoding='utf-8'));assert binary is not None,error
    return ValidationRuntime(sandbox,binary,3000,1024,4096)
def check(runtime,p,text):
    data.validate(p,text);expected=data.oracle(p,text);result=runtime.run(text)
    assert result['status']=='OK' and tokens(result['stdout'].encode())==tokens(expected.encode()),(p,result['status'])
def run(output):
    r=random.Random(data.SEED+77);result={}
    with execute(3) as runtime:
        cases=0
        for z in range(1,11):
            for d in (90,180,270):
                for turn in range(4):
                    origin=[''.join(chr(65+(i*z+j)%26) for j in range(z)) for i in range(z)]
                    L=min(z,10);ops=[(1,1,1,L,d,turn),(2,1,z,1,1,-1),(1,z,1,1,90,(turn+1)%4)]
                    check(runtime,3,data.image_input(origin,z,ops));cases+=1
        for z,shape in [(40,(1,40)),(40,(40,1)),(40,(39,38)),(60,(60,60))]:
            check(runtime,3,data.make_c(r,z,400,shape=shape));cases+=1
        result['image']=dict(status='PASS',cases=cases,method='Forward physical matrices + literal inverse; all d/r choices, rectangular padding and edge coordinates')
    with execute(4) as runtime:
        cases=0
        for n in range(1,101):
            for op in (0,1):check(runtime,4,f'{op} {n}\n');cases+=1
        result['numberTheory']=dict(status='PASS',cases=cases,method='Literal seven-value distinctness over all C,E divisors; no inclusion-exclusion oracle')
    multiset=[v for size in range(1,5) for v in itertools.combinations_with_replacement(range(8),size)]
    checks=0;traces=0
    with execute(5) as runtime:
        for W in range(1,17):
            bags=[[0]]+[[] for _ in multiset];ops=[];expected=[];running=1
            for u,values in enumerate(multiset,2):
                for value in values:ops.append((1,u,value))
                exact=data.brute_colors(values,W)
                assert exact==data.flow_cost(data.Counter(values),W)
                running+=exact;ops.append((3,));expected.append(running);checks+=1
            text=data.encode_e(W,bags,ops);data.validate(5,text);actual=runtime.run(text)
            assert actual['status']=='OK' and list(map(int,actual['stdout'].split()))==expected
            traces+=1
        for i in range(64):
            text=data.make_e(r,r.randint(1,8),r.randint(1,100),r.randint(20,100),10**9,W=r.choice([1,2,3,31,32,33,65535,65536,65537,500000003,2**29-1,2**30,2**40]))
            check(runtime,5,text);traces+=1
        result['packets']=dict(status='PASS',multisetColoringChecks=checks,liveReferenceTraces=traces,method='Stable-subset partition DP (multiplicity kept) + independent weighted matching; dynamic unrestricted 30-bit weights')
    output.mkdir(parents=True,exist_ok=True);(output/'202512-probe.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='/output');run(Path(p.parse_args().output))
