"""Joint maximum-size random costs with independently certified extreme budgets."""
from pathlib import Path
import json,random,sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import data
from sandbox import Sandbox
from validation_runtime import ValidationRuntime
ROOT=Path(__file__).resolve().parent
r=random.Random(data.SEED+12345);n=500000
a=[r.randint(1,10**9) for _ in range(n)];b=[r.randint(1,10**9) for _ in range(n)]
best=10**30;prefix=10**30
for x,y in zip(a,b):prefix=min(prefix,x);best=min(best,prefix+y)
full=sum(a)+sum(b)
cases=[(1,0),(best-1,0),(best,1),(full-1,n-1),(full,n)]
sb=Sandbox('csp-lab-sandbox:local','resource39');binary,error=sb.compile((ROOT/'reference/5.cpp').read_text(encoding='utf-8'));assert binary is not None,error
report=[]
with ValidationRuntime(sb,binary,5000,512,1024) as runtime:
    for budget,answer in cases:
        text=data.encode_e(budget,a,b);data.validate(5,text);result=runtime.run(text)
        assert result['status']=='OK' and result['stdout'].split()==[str(answer)],result
        report.append(dict(n=n,budget=budget,expected=answer,timeMs=result['time_ms'],memoryKb=result['memory_kb']))
Path('/output/202509-resource-probe.json').write_text(json.dumps(dict(status='PASS',cases=report),indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
