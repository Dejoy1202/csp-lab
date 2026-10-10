"""CSP Lab deterministic 202605 data, validation and independent answer models."""
from array import array
from collections import defaultdict,deque
from functools import lru_cache
from pathlib import Path
import bisect,json,random,re,sys,uuid
SEED=2026054205
ROOT=Path(__file__).resolve().parent
ORACLE_DESCRIPTION='Decimal integer arithmetic; reverse daily inventory with exhaustive small counts; independent owner-map segment simulation with cycle detection; exact partition DP and parity-map interval oracle; full-state tree DP, exhaustive start-center enumeration, and constructive lexicographic lower bounds'

def parse(position,text):
    rows=text.splitlines()
    if position==1:return rows[1:]
    if position==2:return tuple(map(int,text.split()))
    if position==3:
        n,m=map(int,rows[0].split());processes=[]
        for line in rows[1:]:
            x=line.split();kind=x[0];start=int(x[1]);off=2;patience=0
            if kind!='X':patience=int(x[2]);off=3
            count=int(x[off]);jobs=[(int(x[j]),int(x[j+1])) for j in range(off+1,len(x),2)]
            assert len(jobs)==count;processes.append((kind,start,patience,jobs))
        assert len(processes)==n;return m,processes
    values=list(map(int,text.split()));n=values[0]
    if position==4:
        q=values[1];assert len(values)==2+n+2*q;return values[2:2+n],list(zip(values[2+n::2],values[3+n::2]))
    assert len(values)==2*n-1;return n,list(zip(values[1::2],values[2::2]))

def needed(count,k,m):
    have=0
    for _ in range(m):have=((have+count)*100+99-k)//(100-k)
    return have

def robots(n,k,m):
    lo,hi=0,10**9
    while lo<hi:
        mid=(lo+hi+1)//2
        if needed(mid,k,m)<=n:lo=mid
        else:hi=mid-1
    if n<=10000:
        def direct(count):
            a=n
            for _ in range(m):
                a-=len(range(0,a*k,100));a-=count
                if a<0:return False
            return True
        assert direct(lo) and not direct(lo+1)
        if n<=120:assert lo==max(c for c in range(n+1) if direct(c))
    return lo

def simulate(m,processes):
    # Each owner is maintained as a resource -> process mapping, with running
    # and waiting states represented explicitly; no reference-program state reused.
    count=len(processes);owner={};cursor=[0]*count;remaining=[0]*count;failures=[0]*count;abandoned=[False]*count;end=[-1]*count;profit=[0]*count;seen=set();now=1
    while True:
        state=(tuple(sorted(owner.items())),tuple(cursor),tuple(remaining),tuple(min(failures[i],processes[i][2]+1) for i in range(count)),tuple(abandoned),tuple(max(start-now,0) for kind,start,w,jobs in processes))
        if state in seen:break
        seen.add(state);asks=defaultdict(list);force=defaultdict(list);working=set()
        for i,(kind,start,w,jobs) in enumerate(processes):
            if cursor[i]==len(jobs) or now<start:continue
            if remaining[i]:working.add(i);continue
            target=jobs[cursor[i]][0]
            if kind=='C' and failures[i]>=w:force[target].append(i)
            else:asks[target].append(i)
        for target in sorted(set(asks)|set(force)):
            if target in force:
                winners=force[target];owner[target]=max(winners)
            elif target not in owner:winners=[min(asks[target])];owner[target]=winners[0]
            else:winners=[]
            for i in winners:working.add(i);remaining[i]=processes[i][3][cursor[i]][1]
        release=set()
        for i,(kind,start,w,jobs) in enumerate(processes):
            if cursor[i]==len(jobs) or now<start or i in working:continue
            failures[i]+=1
            if kind=='A' and failures[i]>=w and not abandoned[i]:release.add(i);abandoned[i]=True
            if kind=='B' and failures[i]>=w:working.add(i);remaining[i]=jobs[cursor[i]][1]
        for i in working:profit[i]+=sum(value==i for value in owner.values())
        for i in working:
            remaining[i]-=1
            if remaining[i]==0:
                cursor[i]+=1;failures[i]=0;abandoned[i]=False
                if cursor[i]==len(processes[i][3]):end[i]=now;release.add(i)
        owner={resource:i for resource,i in owner.items() if i not in release};now+=1
    return ''.join(f'{profit[i]} {end[i]-processes[i][1]+1 if end[i]>=0 else -1}\n' for i in range(count))

def partition(a,l,r):
    dp=[0]*(r-l+2)
    for end in range(l,r+1):
        for start in range(l,end+1):
            value=0
            for p in range(start,end+1,2):value^=a[p]
            dp[end-l+1]=max(dp[end-l+1],dp[start-l]+(value==0))
    return dp[-1]

def interval_answers(a,queries):
    n=len(a)
    if n<=100:
        return ''.join(str(partition(a,l-1,r-1))+'\n' for l,r in queries)
    if all(x==a[0] for x in a):
        width=1 if a[0]==0 else 3
        return ''.join(str((r-l+1)//width)+'\n' for l,r in queries)
    prefix=[0]*n
    for i,x in enumerate(a):prefix[i]=x^(prefix[i-2] if i>=2 else 0)
    nearest=[{},{}];finish=array('I',[n+1])*(n+2)
    for i in range(n-1,-1,-1):
        nearest[i%2][prefix[i]]=i+1
        finish[i+1]=min(finish[i+2],nearest[i%2].get(prefix[i-2] if i>=2 else 0,n+1))
    jump=[array('I',(v+1 if v<=n else n+2 for v in finish))];jump[0][0]=n+2
    jumps=0;current=1
    while current<=n:
        current=jump[0][current];jumps+=1
    if jumps<=64:
        def answer(l,r):
            result=0
            while l<=n and finish[l]<=r:result+=1;l=finish[l]+1
            return result
    else:
        while 1<<len(jump)<=n:
            previous=jump[-1];jump.append(array('I',(previous[v] if v<len(previous) else n+2 for v in previous)))
        def answer(l,r):
            result=0
            for power in range(len(jump)-1,-1,-1):
                if jump[power][l]<=r+1:result+=1<<power;l=jump[power][l]
            return result
    return ''.join(str(answer(l,r))+'\n' for l,r in queries)

def tree_dp(n,edges):
    star=[1<<i for i in range(n)];neighbor=[[] for _ in range(n)]
    for u,v in edges:
        u-=1;v-=1;star[u]|=1<<v;star[v]|=1<<u;neighbor[u].append(v);neighbor[v].append(u)
    best={};queue=deque()
    for u in range(n):
        key=(u,star[u]);best[key]=tuple(v+1 for v in range(n) if star[u]>>v&1);queue.append(key)
    while queue:
        u,mask=queue.popleft();sequence=best[u,mask]
        for v in [u]+neighbor[u]:
            added=star[v]&~mask
            left=tuple(x+1 for x in range(sequence[0]-1) if added>>x&1)
            right=tuple(x+1 for x in range(sequence[0],n) if added>>x&1)
            value=left+sequence+right;key=(v,mask|added)
            if key not in best or value<best[key]:best[key]=value;queue.append(key)
    return min(value for (u,mask),value in best.items() if mask==(1<<n)-1)

def breadth_sorted(n,edges):
    # A constructive certificate attains the globally smallest possible
    # permutation when BFS child blocks form consecutive increasing intervals.
    graph=[[] for _ in range(n+1)]
    for u,v in edges:graph[u].append(v);graph[v].append(u)
    parent=[0]*(n+1);queue=[1];expected=2
    for u in queue:
        children=sorted(v for v in graph[u] if v!=parent[u])
        if children!=list(range(expected,expected+len(children))):return False
        expected+=len(children)
        for v in children:parent[v]=u;queue.append(v)
    return expected==n+1

TREE_RUNTIME=None

def tree_enumeration(text):
    global TREE_RUNTIME
    if TREE_RUNTIME is None:
        from sandbox import Sandbox
        from validation_runtime import ValidationRuntime
        sb=Sandbox('csp-lab-sandbox:local','oracle-'+uuid.uuid4().hex)
        binary,error=sb.compile((ROOT/'oracle.cpp').read_text(encoding='utf-8'));assert binary,error
        TREE_RUNTIME=ValidationRuntime(sb,binary,60000,1024,2048)
        import atexit;atexit.register(TREE_RUNTIME.close)
    result=TREE_RUNTIME.run(text);assert result['status']=='OK',result
    return result['stdout']

def oracle(position,text):
    parsed=parse(position,text)
    if position==1:
        numbers=[int(x.replace('.','')) for x in parsed]
        ordinary=[(x+5)//10 for x in numbers]
        bankers=[int(round(x/10)) for x in numbers]  # exact tenths within small bounded integers
        return ' '.join(map(str,ordinary))+'\n'+' '.join(map(str,bankers))+'\n'
    if position==2:return str(robots(*parsed))+'\n'
    if position==3:return simulate(*parsed)
    if position==4:return interval_answers(*parsed)
    n,edges=parsed
    if n<=10:
        answer=' '.join(map(str,tree_dp(n,edges)))+'\n'
        assert answer.split()==tree_enumeration(text).split()
        return answer
    if breadth_sorted(n,edges):return ' '.join(map(str,range(1,n+1)))+'\n'
    return tree_enumeration(text)

def validate(position,text):
    assert text.endswith('\n')
    parsed=parse(position,text)
    if position==1:
        assert 1<=len(parsed)<=100 and int(text.splitlines()[0])==len(parsed)
        assert all(re.fullmatch(r'[0-9]+\.[0-9]',x) and int(x[:-2])<=100000 for x in parsed)
    elif position==2:
        n,k,m=parsed;assert 1<=n<=10**18 and 1<=k<=5 and 1<=m<=2000
        answer=robots(n,k,m);assert 1<=answer<=10**9 and needed(10**9+1,k,m)>n
    elif position==3:
        m,processes=parsed;assert 1<=m<=40 and 1<=len(processes)<=10
        for kind,start,w,jobs in processes:
            assert kind in 'XABC' and 1<=start<=20 and (kind=='X' or 1<=w<=20) and 1<=len(jobs)<=40
            assert len({a for a,t in jobs})==len(jobs) and all(1<=a<=m and 1<=t<=20 for a,t in jobs)
    elif position==4:
        a,queries=parsed;assert 1<=len(a)<=10**6 and 1<=len(queries)<=10**6
        assert all(0<=x<2**31 for x in a) and all(1<=l<=r<=len(a) for l,r in queries)
    else:
        n,edges=parsed;assert 2<=n<=100000 and len(edges)==n-1;parent=list(range(n+1))
        def root(u):
            while parent[u]!=u:parent[u]=parent[parent[u]];u=parent[u]
            return u
        for u,v in edges:
            assert 1<=u<=n and 1<=v<=n and u!=v
            a,b=root(u),root(v);assert a!=b;parent[a]=b
        assert len({root(i) for i in range(1,n+1)})==1

def numbers(values):return str(len(values))+'\n'+'\n'.join(f'{a}.{b}' for a,b in values)+'\n'
def process_input(m,processes):return f'{len(processes)} {m}\n'+''.join(kind+' '+str(start)+' '+(str(w)+' ' if kind!='X' else '')+str(len(jobs))+' '+ ' '.join(f'{a} {t}' for a,t in jobs)+'\n' for kind,start,w,jobs in processes)
def array_input(a,queries):return f'{len(a)} {len(queries)}\n'+' '.join(map(str,a))+'\n'+''.join(f'{l} {r}\n' for l,r in queries)
def tree_input(n,edges):return str(n)+'\n'+''.join(f'{u} {v}\n' for u,v in edges)
def random_tree(rng,n):return [(i,rng.randrange(1,i)) for i in range(2,n+1)]
def shuffled_tree(rng,n):
    labels=list(range(1,n+1));rng.shuffle(labels);edges=random_tree(rng,n);return [(labels[u-1],labels[v-1]) for u,v in edges]
def random_processes(rng,m,n,kinds):return [(rng.choice(kinds),rng.randint(1,20),rng.randint(1,20),[(a,rng.randint(1,20)) for a in rng.sample(range(1,m+1),rng.randint(1,m))]) for _ in range(n)]

def small_cases(position):
    rng=random.Random(SEED+position)
    for i in range(40):
        if position==1:yield numbers([(rng.randint(0,100000),rng.randrange(10)) for _ in range(rng.randint(1,100))])
        elif position==2:
            k=rng.randint(1,5);m=rng.randint(1,8);count=rng.randint(1,5);n=needed(count,k,m)+rng.randrange(3);yield f'{n} {k} {m}\n'
        elif position==3:
            m=rng.randint(1,8);yield process_input(m,random_processes(rng,m,rng.randint(1,6),'XABC'))
        elif position==4:
            n=rng.randint(1,25);a=[rng.randrange(8) for _ in range(n)];queries=[]
            for _ in range(10):l=rng.randint(1,n);queries.append((l,rng.randint(l,n)))
            yield array_input(a,queries)
        else:
            n=rng.randint(2,10);yield tree_input(n,shuffled_tree(rng,n))

def dataset(position):
    rng=random.Random(SEED+100+position)
    if position==1:
        cases=[numbers([(0,0)]),numbers([(100000,9)]),numbers([(a,b) for a,b in [(0,4),(1,6),(99999,9),(100000,0)]]),numbers([(i,b) for i,b in enumerate([0,1,2,3,4,6,7,8,9])])]
        for i in range(6):cases.append(numbers([(rng.randrange(100001),rng.choice([0,1,2,3,4,6,7,8,9])) for _ in range(10+15*i)]))
        cases.extend([numbers([(0,5)]),numbers([(1,5)]),numbers([(100000,5)]),numbers([(99999,5)]),numbers([(i,5) for i in range(100)])])
        for i in range(5):cases.append(numbers([(rng.randrange(100001),5 if j%2==0 else rng.randrange(10)) for j in range(100)]))
        return cases
    if position==2:
        cases=['2 1 1\n','2 5 1\n','3 5 1\n','10 1 2\n','9999 5 20\n','10000 1 50\n']
        for i in range(10):
            k=rng.randint(1,5);m=rng.randint(1,30);count=rng.randint(1,20);n=needed(count,k,m)+rng.randrange(3);assert n<=10000;cases.append(f'{n} {k} {m}\n')
        cases.extend(['1000000000000000000 1 2000\n','1000000000000000000 5 700\n',f'{needed(1,1,2000)} 1 2000\n',f'{needed(10**9,1,1000)} 1 1000\n'])
        return cases
    if position==3:
        cases=[process_input(2,[('X',1,0,[(1,1),(2,1)]),('X',1,0,[(2,1),(1,1)])]),process_input(1,[('X',1,0,[(1,1)]),('X',1,0,[(1,2)])]),process_input(4,[('X',20,0,[(1,20),(2,20),(3,20),(4,20)])])]
        for _ in range(5):cases.append(process_input(40,random_processes(rng,40,10,'X')))
        cases.extend([process_input(2,[('A',1,1,[(1,1),(2,2)]),('X',1,0,[(2,1),(1,3)])]),process_input(1,[('X',1,0,[(1,20)]),('B',2,1,[(1,2)])]),process_input(3,[('A',1,2,[(1,1),(2,1),(3,1)]),('A',1,1,[(2,1),(1,1),(3,1)]),('B',1,3,[(3,4),(1,2)])])])
        for _ in range(5):cases.append(process_input(40,random_processes(rng,40,10,'XAB')))
        cases.extend([process_input(1,[('X',1,0,[(1,20)]),('C',1,1,[(1,3)]),('C',1,1,[(1,4)]),('B',1,2,[(1,2)])]),process_input(2,[('X',1,0,[(1,2),(2,20)]),('C',1,2,[(1,4),(2,1)]),('C',1,1,[(2,3),(1,2)])]),process_input(40,[('C' if i%3==0 else 'ABX'[i%3],1,20,[(a,20) for a in rng.sample(range(1,41),40)]) for i in range(10)]),process_input(40,random_processes(rng,40,10,'XABC'))])
        return cases
    if position==4:
        cases=[]
        for n in [1,2,3,5,20,100]:
            a=[0] if n==1 else [rng.randrange(8) for _ in range(n)];queries=[(1,n),(n,n),(1,1)]+[(l,r) for l in range(1,min(n,8)+1) for r in range(l,min(n,8)+1)];cases.append(array_input(a,queries))
        for i in range(6):
            n=100+500*i;a=[rng.randrange(1<<min(31,3+5*i)) for _ in range(n)];queries=[(1,n),(n,n)]+[(l,rng.randint(l,n)) for l in (rng.randint(1,n) for _ in range(200+i*500))];cases.append(array_input(a,queries))
        for i in range(4):
            n=100000;a=[rng.randrange(16 if i<2 else 1<<31) for _ in range(n)];queries=[(1,n),(n,n),(1,1)]+[(l,rng.randint(l,n)) for l in (rng.randint(1,n) for _ in range(99997))];cases.append(array_input(a,queries))
        for i in range(4):
            n=1000000;a=[0]*n if i==0 else ([2147483647]*n if i==1 else [rng.randrange(8 if i==2 else 1<<31) for _ in range(n)]);queries=[(1,n),(n,n),(1,1)]+[(l,rng.randint(l,n)) for l in (rng.randint(1,n) for _ in range(999997))];cases.append(array_input(a,queries))
        return cases
    cases=[]
    for n in [2,4,7,10]:cases.append(tree_input(n,shuffled_tree(rng,n)))
    for n in [40,100,300,500]:cases.append(tree_input(n,shuffled_tree(rng,n)))
    for n in [800,1500,3000,2999]:cases.append(tree_input(n,shuffled_tree(rng,n)))
    for kind in ['chain','star','binary','breadth-random']:
        n=100000
        if kind=='chain':edges=[(i-1,i) for i in range(2,n+1)]
        elif kind=='star':edges=[(1,i) for i in range(2,n+1)]
        elif kind=='binary':edges=[(i//2,i) for i in range(2,n+1)]
        else:
            # Relabel a general random rooted shape in breadth-first order.
            original=random_tree(rng,n);g=[[] for _ in range(n+1)]
            for u,v in original:g[u].append(v);g[v].append(u)
            order=[1];parent=[0]*(n+1)
            for u in order:
                for v in g[u]:
                    if v!=parent[u]:parent[v]=u;order.append(v)
            labels={u:i+1 for i,u in enumerate(order)};edges=[(labels[u],labels[v]) for u,v in original]
        cases.append(tree_input(n,edges))
    for kernel in [8,32,80,160]:
        n=100000;edges=random_tree(rng,kernel)+[(i,rng.randint(1,kernel)) for i in range(kernel+1,n+1)];labels=list(range(1,n+1));rng.shuffle(labels);cases.append(tree_input(n,[(labels[u-1],labels[v-1]) for u,v in edges]))
    return cases

def configure_scoring(position,tests):
    if position not in (4,5):return tests,[]
    sizes=[6,6,4,4] if position==4 else [4,4,4,8];scores=[30,30,20,20] if position==4 else [20,20,20,40];limits=[100,3000,100000,1000000] if position==4 else [10,500,3000,100000];groups=[];offset=0
    for i,(count,score,limit) in enumerate(zip(sizes,scores,limits),1):
        key='scale-'+str(i);groups.append(dict(key=key,score=score,label=f'本站模拟子任务：规模不超过{limit}'))
        for test in tests[offset:offset+count]:test['score']=0;test['subtaskKey']=key
        offset+=count
    return tests,groups


def extra_assets(position):
    if position!=5:return []
    return [dict(name='oracle.cpp',kind='VALIDATOR',content=(ROOT/'oracle.cpp').read_text(encoding='utf-8')),dict(name='probe_e.py',kind='VALIDATOR',content=(ROOT/'probe_e.py').read_text(encoding='utf-8'))]
