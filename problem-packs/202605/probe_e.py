"""Independent complete-state DP versus the 202605 tree reference, in Docker."""
from collections import deque
from itertools import product
from pathlib import Path
import random,json,uuid
from sandbox import Sandbox,tokens
from validation_runtime import ValidationRuntime
ROOT=Path(__file__).resolve().parent

def dp_tree(n,edges):
    neighbors=[[] for _ in range(n)]
    stars=[1<<i for i in range(n)]
    for u,v in edges:
        neighbors[u].append(v);neighbors[v].append(u);stars[u]|=1<<v;stars[v]|=1<<u
    best={};queue=deque()
    for u in range(n):
        key=(u,stars[u]);best[key]=tuple(v for v in range(n) if stars[u]>>v&1);queue.append(key)
    while queue:
        u,mask=queue.popleft();sequence=best[u,mask]
        for v in [u]+neighbors[u]:
            added=stars[v]&~mask
            left=tuple(x for x in range(sequence[0]) if added>>x&1)
            right=tuple(x for x in range(sequence[0]+1,n) if added>>x&1)
            value=left+sequence+right;key=(v,mask|added)
            if key not in best or value<best[key]:best[key]=value;queue.append(key)
    return min(value for (u,mask),value in best.items() if mask==(1<<n)-1)

def prufer(seq,n):
    degree=[1]*n
    for x in seq:degree[x]+=1
    edges=[]
    for x in seq:
        leaf=next(i for i,d in enumerate(degree) if d==1);edges.append((leaf,x));degree[leaf]-=1;degree[x]-=1
    left=[i for i,d in enumerate(degree) if d==1];edges.append(tuple(left));return edges

def text(n,edges):return str(n)+'\n'+''.join(f'{u+1} {v+1}\n' for u,v in edges)

def main():
    sb=Sandbox('csp-lab-sandbox:local','probe-'+uuid.uuid4().hex)
    binary,error=sb.compile((ROOT/'reference/5.cpp').read_text(encoding='utf-8'));assert binary,error
    count=0;rng=random.Random(20260542)
    with ValidationRuntime(sb,binary,3000,1024,2048) as runtime:
        for n in range(2,6):
            for sequence in product(range(n),repeat=n-2):
                edges=prufer(sequence,n);expected=dp_tree(n,edges);actual=runtime.run(text(n,edges));assert actual['status']=='OK',(n,edges,actual);assert tuple(int(x)-1 for x in actual['stdout'].split())==expected,(n,edges,actual,expected);count+=1
            print(f'T5 complete-state DP: all labelled trees with n={n} passed',flush=True)
        for n in [6,7,8,9,10]:
            for _ in range(30):
                edges=prufer([rng.randrange(n) for i in range(n-2)],n);expected=dp_tree(n,edges);actual=runtime.run(text(n,edges));assert actual['status']=='OK',(n,edges,actual);assert tuple(int(x)-1 for x in actual['stdout'].split())==expected,(n,edges,actual,expected);count+=1
            print(f'T5 complete-state DP: 30 trees with n={n} passed',flush=True)
    Path('/output/202605-e-probe.json').write_text(json.dumps(dict(status='PASS',completeStateDifferentialCases=count),indent=2),encoding='utf-8')
if __name__=='__main__':main()
