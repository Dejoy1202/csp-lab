"""Joint maximum n/q/initial population and full-width Trie, independent W=1 certificate."""
import hashlib,json,random,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT.parent))
from sandbox import Sandbox
from validation_runtime import ValidationRuntime
n=500000;r=random.Random(202512400599);a=[r.randrange(1<<29) for _ in range(n)]
rows=[f'{n} 1']+[f'1 {x}' for x in a]+[str(n)]
rows += [f'1 {i+1} {a[i]^((1<<29)-1)}' for i in range(n-1)]+['3']
text='\n'.join(rows)+'\n'
# W=1: only identical values conflict. The original and inserted values in each bag are distinct,
# so each of n bags needs exactly one color, independent of trie/graph matching.
assert all(a[i]!=(a[i]^((1<<29)-1)) for i in range(n-1))
sandbox=Sandbox('csp-lab-sandbox:local','memory-'+uuid.uuid4().hex)
binary,error=sandbox.compile((ROOT/'reference/5.cpp').read_text(encoding='utf-8'));assert binary is not None,error
with ValidationRuntime(sandbox,binary,3000,1024) as runtime:
    result=runtime.run(text)
    assert result['status']=='OK' and result['stdout'].split()==[str(n)],result['status']
report=dict(status='PASS',n=n,q=n,initialElements=n,finalElements=2*n-1,W=1,
    inputSha256=hashlib.sha256(text.encode()).hexdigest(),expectedSystemCost=n,
    referenceTimeMs=result['time_ms'],referenceMemoryKb=result['memory_kb'],
    method='For W=1, max equal-value multiplicity; each active packet has one or two distinct values')
Path('/output/202512-memory-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
