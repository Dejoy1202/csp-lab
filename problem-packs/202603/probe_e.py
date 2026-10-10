"""Small exhaustive station choices and separate direct-tire simulation."""
from collections import deque
from itertools import product
from pathlib import Path
import importlib.util,json,random,uuid
from sandbox import Sandbox
from validation_runtime import ValidationRuntime
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('data603',ROOT/'data.py');data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)

def tree_from_prufer(n,seq):
    degree=[1]*(n+1)
    for v in seq:degree[v]+=1
    result=[]
    for v in seq:
        leaf=next(i for i in range(1,n+1) if degree[i]==1);result.append((leaf,v));degree[leaf]-=1;degree[v]-=1
    left=[i for i in range(1,n+1) if degree[i]==1];result.append(tuple(left));return result

def main():
    rng=random.Random(2026034133);sandbox=Sandbox('csp-lab-sandbox:local','probe-'+uuid.uuid4().hex);binary,message=sandbox.compile((ROOT/'reference/5.cpp').read_text(encoding='utf-8'));assert binary,message
    exhaustive=0;random_count=0
    with ValidationRuntime(sandbox,binary,5000,1024,1024) as runtime:
        def check(n,edges,stations):
            plans=[(s,t) for s in range(1,n+1) for t in range(1,n+1) if s!=t];repair=edges.copy();rng.shuffle(repair);events=[(2,)]
            for u,v in repair:events.extend([(1,u,v),(2,),(2,)])
            expected=data.travel_brute(n,edges,stations,plans,events);last=0;answers=iter(map(int,expected.split()));encoded=[]
            for op in events:
                if op[0]==2:last=next(answers);encoded.append(op)
                else:encoded.append((1,op[1]^last,op[2]^last))
            text=data.render_e(n,1,edges,stations,plans,encoded);observed=runtime.run(text);assert observed['status']=='OK' and observed['stdout'].split()==expected.split(),(n,edges,stations,observed)
            assert data.helper('oracle.cpp',data.render_e(n,0,edges,stations,plans,events)).split()==expected.split()
        for n in range(2,5):
            for seq in product(range(1,n+1),repeat=n-2):
                edges=tree_from_prufer(n,seq)
                for mask in range(1,1<<n):
                    check(n,edges,[v for v in range(1,n+1) if mask>>(v-1)&1]);exhaustive+=1
                    if exhaustive%50==0:print(f'exhaustive station checks: {exhaustive}',flush=True)
        for n in range(5,13):
            for _ in range(10):
                edges,_=data.make_tree(rng,n,rng.choice(['chain','star','binary','random']));check(n,edges,rng.sample(range(1,n+1),rng.randint(1,n)));random_count+=1
    report=dict(status='PASS',exhaustiveLabelledTreeAndStationCases=exhaustive,randomCases=random_count,totalChecks=exhaustive+random_count,allOrderedPairs=True,onlineEncryptedEvents=True,oracle='Direct BFS paths and tire simulation, plus offline repair-time oracle')
    Path('/output/202603-e-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
