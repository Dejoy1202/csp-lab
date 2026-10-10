"""Future high digits, maximum R, composite bases and block boundary probes."""
from pathlib import Path
import importlib.util,json,random,uuid
from sandbox import Sandbox
from validation_runtime import ValidationRuntime
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('data603',ROOT/'data.py');data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
rng=random.Random(2026034104);sandbox=Sandbox('csp-lab-sandbox:local','probe-d-'+uuid.uuid4().hex);binary,message=sandbox.compile((ROOT/'reference/4.cpp').read_text(encoding='utf-8'));assert binary,message
count=0;literal=0
with ValidationRuntime(sandbox,binary,6000,1024,1024) as runtime:
    for k in (11,13,15,999983,999999999):
        cap=k
        while cap*k<=10**12+1:cap*=k
        fixtures=[([0],[(2,1,1),(1,1,1,0),(2,1,1)]),([k-1,1,0],[(2,1,3),(1,1,3,1),(2,1,3),(1,2,3,k),(2,1,3)]),([0,0,0],[(2,1,3),(1,1,3,10**12),(2,1,3),(2,1,1),(1,2,2,0),(2,2,3)])]
        # The second fixture needs no new high digit beyond k^2, which is <=1e12 only for small bases.
        if k>10**8:fixtures[1]=([k-1,1,0],[(2,1,3),(1,1,3,1),(2,1,3),(1,2,3,0),(2,1,3)])
        a=[rng.randrange(cap) for _ in range(1403)];ops=[(2,1,1403),(1,699,701,rng.randrange(cap)),(2,699,701),(1,1,1403,rng.randrange(cap)),(2,1,1403),(2,700,1403)]
        fixtures.append((a,ops))
        for a,ops in fixtures:
            text=data.make_d(k,a,ops);expected=data.xor_naive(k,a.copy(),ops);observed=runtime.run(text);assert observed['status']=='OK' and observed['stdout'].split()==expected.split(),(k,observed)
            assert data.helper('oracle_d.cpp',text).split()==expected.split();count+=1
    for k in range(11,60,2):
        answer=0
        for x in range(512):
            if x:answer=data.xor_base(x,answer,k)
            assert answer==data.formula(x,k);literal+=1
report=dict(status='PASS',boundaryCases=count,literalRecurrenceChecks=literal,checks=['all-zero initial array followed by 10^12 update','new higher digits after initialization','odd composite bases','wrapping least digit','partial update crossing 700-element oracle blocks','k near 10^9'])
Path('/output/202603-d-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
