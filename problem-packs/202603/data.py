"""Independent 202603 generators, input validators, and answer certificates."""
from bisect import bisect_left,insort
from collections import deque
from fractions import Fraction
from decimal import Decimal,localcontext
from pathlib import Path
import atexit,hashlib,json,random,uuid
SEED=2026034105
ROOT=Path(__file__).resolve().parent
ORACLE_DESCRIPTION='Binary string counts; exact Fraction marginal knapsack with exhaustive small subsets; occupied-interval allocator; literal recurrence and independent sqrt decomposition; offline second-latest repair times cross-checked by BFS tire simulation'
RUNTIME={};TRAVEL={};CERTIFICATES=[]

def helper(name,text):
    if name not in RUNTIME:
        from sandbox import Sandbox
        from validation_runtime import ValidationRuntime
        sandbox=Sandbox('csp-lab-sandbox:local','oracle-'+uuid.uuid4().hex)
        binary,message=sandbox.compile((ROOT/name).read_text(encoding='utf-8'))
        assert binary is not None,message
        RUNTIME[name]=ValidationRuntime(sandbox,binary,30000,1024,4096)
        atexit.register(RUNTIME[name].close)
    result=RUNTIME[name].run(text)
    assert result['status']=='OK',result
    return result['stdout']

def parse(position,text):
    rows=text.splitlines()
    if position==1:
        v=list(map(int,text.split()));assert len(v)==v[0]+1;return v[1:]
    if position==2:
        n,m=map(int,rows[0].split());tasks=[tuple(map(int,row.split())) for row in rows[1:]];assert len(tasks)==n;return m,tasks
    if position==3:
        n,q=map(int,rows[0].split());ops=[row.split() for row in rows[1:]];assert len(ops)==q;return n,ops
    if position==4:
        n,q,k=map(int,rows[0].split());a=list(map(int,rows[1].split()));ops=[tuple(map(int,row.split())) for row in rows[2:]];assert len(a)==n and len(ops)==q;return k,a,ops
    it=iter(map(int,text.split()));n,X=next(it),next(it);edges=[(next(it),next(it)) for _ in range(n-1)];k=next(it);stations=[next(it) for _ in range(k)];m=next(it);plans=[(next(it),next(it)) for _ in range(m)];q=next(it);events=[]
    for _ in range(q):
        kind=next(it);events.append((kind,next(it),next(it)) if kind==1 else (kind,))
    assert next(it,None) is None;return n,X,edges,stations,plans,events

def balanced(a):return sum(bin(x)[2:].count('0')==bin(x)[2:].count('1') for x in a)

def coffee(budget,tasks):
    regular=[(a,b) for o,t,a,b in tasks if o==1]
    marginal=sorted((Fraction(b,a) for o,t,a,b in tasks if o==0 for _ in range(a)),reverse=True)
    prefix=[Fraction(0)]
    for x in marginal[:budget]:prefix.append(prefix[-1]+x)
    def flex(left):return prefix[min(left,len(prefix)-1)]
    states={0:0}
    for a,b in regular:
        new=dict(states)
        for used,gain in states.items():
            if used+a<=budget:new[used+a]=max(new.get(used+a,-1),gain+b)
        states=new
    best=max(Fraction(gain)+flex(budget-used) for used,gain in states.items())
    if len(regular)<=12:
        exhaustive=Fraction(0)
        for mask in range(1<<len(regular)):
            used=sum(a for i,(a,b) in enumerate(regular) if mask>>i&1)
            if used<=budget:exhaustive=max(exhaustive,sum(b for i,(a,b) in enumerate(regular) if mask>>i&1)+flex(budget-used))
        assert best==exhaustive
    return Fraction(sum(t for o,t,a,b in tasks))-best

def allocation(n,operations):
    processes=[[] for _ in range(n+1)];occupied=[];output=[]
    for fields in operations:
        op,p=fields[0],int(fields[1])
        if op=='new':
            length=int(fields[2]);last=0;options=[]
            for start,size in occupied:
                if start-last>=length:options.append((start-last,last))
                last=start+size
            address=min(options)[1] if options else last
            insort(occupied,(address,length));processes[p].append([address,length,0]);output.append(address)
        elif op=='send':
            assert processes[p];total=0
            for queue in processes[p]:
                start,length,sent=queue;total+=start+sent%length;queue[2]+=1
            output.append(total)
        else:
            index=int(fields[2])-1;queue=processes[p].pop(index);at=bisect_left(occupied,(queue[0],queue[1]));assert occupied[at]==tuple(queue[:2]);occupied.pop(at)
    return ''.join(str(x)+'\n' for x in output)

def xor_base(a,b,k):
    answer,power=0,1
    while a or b:
        answer+=(a%k+b%k)%k*power;a//=k;b//=k;power*=k
    return answer

def formula(x,k):
    low=x%k;answer=low*(low+1)//2%k;power=k;x//=k
    while x:
        answer+=x%k*(low+1)%k*power;x//=k;power*=k
    return answer

def xor_naive(k,a,operations):
    table=None
    if max(a+[op[3] for op in operations if op[0]==1]+[0])<=500:
        # Literal f recurrence, no digit formula used for expected values.
        power=k
        while power<=500:power*=k
        if power<=10000:
            table=[0]*power
            for x in range(1,power):table[x]=xor_base(x,table[x-1],k)
            assert all(table[x]==formula(x,k) for x in range(power))
    out=[]
    for op in operations:
        kind,l,r=op[:3]
        if kind==1:
            for i in range(l-1,r):a[i]=xor_base(a[i],op[3],k);assert a[i]<=10**12
        else:
            answer=0
            for x in a[l-1:r]:answer=xor_base(answer,table[x] if table is not None else formula(x,k),k)
            out.append(answer)
    return ''.join(str(x)+'\n' for x in out)

def travel_brute(n,edges,stations,plans,events,X=0):
    graph=[[] for _ in range(n+1)]
    for i,(u,v) in enumerate(edges):graph[u].append((v,i));graph[v].append((u,i))
    paths=[]
    for s,t in plans:
        parent={s:(0,-1)};queue=deque([s])
        while t not in parent:
            u=queue.popleft()
            for v,e in graph[u]:
                if v not in parent:parent[v]=(u,e);queue.append(v)
        path=[];v=t
        while v!=s:u,e=parent[v];path.append((e,v));v=u
        paths.append(path[::-1])
    lookup={tuple(sorted(edge)):i for i,edge in enumerate(edges)};repaired=set();stations=set(stations);last=0;out=[]
    for op in events:
        if op[0]==1:
            pair=tuple(sorted((op[1]^(X*last),op[2]^(X*last))));assert pair in lookup and lookup[pair] not in repaired;repaired.add(lookup[pair])
        else:
            answer=0
            for path in paths:
                broken=0;valid=True
                for e,v in path:
                    if e not in repaired:broken+=1
                    if broken>=2:valid=False;break
                    if v in stations:broken=0
                answer+=valid
            last=answer;out.append(answer)
    return ''.join(str(x)+'\n' for x in out)

def render_e(n,X,edges,stations,plans,events):
    return f'{n} {X}\n'+''.join(f'{u} {v}\n' for u,v in edges)+f'{len(stations)}\n'+' '.join(map(str,stations))+'\n'+f'{len(plans)}\n'+''.join(f'{s} {t}\n' for s,t in plans)+f'{len(events)}\n'+''.join(' '.join(map(str,op))+'\n' for op in events)

def prepare_e(n,X,edges,stations,plans,plain):
    raw=render_e(n,0,edges,stations,plans,plain);expected=helper('oracle.cpp',raw)
    if n<=100:assert expected==travel_brute(n,edges,stations,plans,plain)
    answers=iter(map(int,expected.split()));last=0;encoded=[]
    for op in plain:
        if op[0]==2:last=next(answers);encoded.append(op)
        else:encoded.append((1,op[1]^(X*last),op[2]^(X*last)))
    text=render_e(n,X,edges,stations,plans,encoded);digest=hashlib.sha256(text.encode()).hexdigest();TRAVEL[digest]=(expected,plain)
    CERTIFICATES.append(dict(inputSha256=digest,decodedOperationsSha256=hashlib.sha256(raw.encode()).hexdigest(),answerSha256=hashlib.sha256(expected.encode()).hexdigest(),method='second-latest road repair times; small inputs also direct BFS tires'))
    return text

def oracle(position,text):
    data=parse(position,text)
    if position==1:return str(balanced(data))+'\n'
    if position==2:
        value=coffee(*data)
        with localcontext() as ctx:ctx.prec=50;return format(Decimal(value.numerator)/Decimal(value.denominator),'.15f')+'\n'
    if position==3:return allocation(*data)
    if position==4:
        k,a,ops=data
        if len(a)<=1000:
            answer=xor_naive(k,a,ops)
            if len(a)<=100:assert answer.split()==helper('oracle_d.cpp',text).split(), 'Independent digit oracle mismatch'
            return answer
        return helper('oracle_d.cpp',text)
    digest=hashlib.sha256(text.encode()).hexdigest()
    if digest in TRAVEL:return TRAVEL[digest][0]
    n,X,edges,stations,plans,events=data
    if n<=100:return travel_brute(n,edges,stations,plans,events,X)
    assert X==0,'For large encrypted input, run deterministic dataset generation first to create independently computed decoding certificates'
    return helper('oracle.cpp',text)

def compare(position,text,actual,expected):
    if position!=2:return actual.split()==expected.split()
    fields=actual.split()
    if len(fields)!=1:return False
    try:return abs(Decimal(fields[0])-Decimal(expected))<Decimal('0.000000001')
    except Exception:return False

def validate(position,text):
    data=parse(position,text)
    if position==1:assert 1<=len(data)<=100 and all(1<=x<=10**9 for x in data);return
    if position==2:
        budget,tasks=data;assert 1<=budget<=1000 and 1<=len(tasks)<=200
        assert all(o in (0,1) and 1<=a<=100 and 1<=b<t<=10000 for o,t,a,b in tasks);return
    if position==3:
        n,ops=data;assert 1<=n<=100 and 1<=len(ops)<=8000;counts=[0]*(n+1)
        for fields in ops:
            assert fields[0] in ('new','send','delete');p=int(fields[1]);assert 1<=p<=n
            if fields[0]=='new':assert len(fields)==3 and 1<=int(fields[2])<=500000;counts[p]+=1
            elif fields[0]=='send':assert len(fields)==2 and counts[p]>0
            else:assert len(fields)==3 and 1<=int(fields[2])<=counts[p];counts[p]-=1
        return
    if position==4:
        k,a,ops=data;assert 11<=k<=10**9 and k%2==1 and 1<=len(a)<=500000 and 1<=len(ops)<=10000
        assert all(0<=x<=10**12 for x in a)
        for op in ops:assert op[0] in (1,2) and 1<=op[1]<=op[2]<=len(a) and len(op)==(4 if op[0]==1 else 3) and (op[0]==2 or 0<=op[3]<=10**12)
        if len(a)<=1000:xor_naive(k,a.copy(),ops)
        else:
            shifts=[op[3] for op in ops if op[0]==1];power=k
            while power*k<=10**12+1:power*=k
            assert max(a+shifts)<power or (all(v<k for v in shifts) and max(a)<=10**12-(k-1)) or all(v==0 for v in shifts),'Missing full-scale invariant certificate'
        return
    n,X,edges,stations,plans,events=data;assert 2<=n<=100000 and X in (0,1) and 1<=len(stations)<=min(n,20) and len(set(stations))==len(stations)
    assert all(1<=v<=n for v in stations) and 1<=len(plans)<=100000 and 1<=len(events)<=200000
    parents=list(range(n+1))
    def find(v):
        while v!=parents[v]:parents[v]=parents[parents[v]];v=parents[v]
        return v
    for u,v in edges:
        assert 1<=u<=n and 1<=v<=n and find(u)!=find(v);parents[find(u)]=find(v)
    assert all(1<=s<=n and 1<=t<=n and s!=t for s,t in plans)
    expected=oracle(5,text);answers=iter(map(int,expected.split()));lookup={tuple(sorted(e)) for e in edges};seen=set();last=0;decoded=[]
    for op in events:
        assert op[0] in (1,2)
        if op[0]==2:last=next(answers);assert 0<=last<=len(plans);decoded.append(op)
        else:
            assert len(op)==3 and op[1]>=0 and op[2]>=0;u,v=op[1]^(X*last),op[2]^(X*last);pair=tuple(sorted((u,v)));assert pair in lookup and pair not in seen;seen.add(pair);decoded.append((1,u,v))
    assert next(answers,None) is None
    certificate=TRAVEL.get(hashlib.sha256(text.encode()).hexdigest())
    if certificate:assert decoded==certificate[1]


def make_a(a):return str(len(a))+'\n'+' '.join(map(str,a))+'\n'
def make_b(m,tasks):return f'{len(tasks)} {m}\n'+''.join(' '.join(map(str,t))+'\n' for t in tasks)
def make_c(n,ops):return f'{n} {len(ops)}\n'+''.join(' '.join(map(str,op))+'\n' for op in ops)
def make_d(k,a,ops):return f'{len(a)} {len(ops)} {k}\n'+' '.join(map(str,a))+'\n'+''.join(' '.join(map(str,op))+'\n' for op in ops)

def random_c(rng,n,q,limit,deleted=True):
    ops=[];counts=[0]*(n+1)
    for step in range(q):
        active=[p for p in range(1,n+1) if counts[p]]
        kind=rng.random()
        if not active or kind<.45:
            p=rng.randint(1,n);ops.append(('new',p,rng.choice([1,limit,rng.randint(1,limit)])));counts[p]+=1
        elif deleted and kind<.7:
            p=rng.choice(active);ops.append(('delete',p,rng.randint(1,counts[p])));counts[p]-=1
        else:ops.append(('send',rng.choice(active)))
    return make_c(n,ops)

def random_d(rng,n,q,k,cap,multiples=False):
    power=k
    while power*k<=cap+1:power*=k
    if multiples:
        values=[rng.randrange(max(1,power//k))*k for _ in range(n)]
    else:values=[rng.randrange(power) for _ in range(n)]
    if n>1000 and k>10**8:
        values=[rng.randrange(900)*k+rng.randrange(k) for _ in range(n)]
    ops=[(2,1,n)]
    for i in range(1,q):
        mode=i%7
        if mode==0:l,r=1,n
        elif mode==1:l=r=rng.randint(1,n)
        elif mode==2:l,r=1,rng.randint(1,n)
        elif mode==3:l,r=rng.randint(1,n),n
        else:l,r=sorted((rng.randint(1,n),rng.randint(1,n)))
        if i%3==0:ops.append((2,l,r))
        else:
            value=rng.randrange(power)
            if multiples:value=value//k*k
            if n>1000 and k>10**8:value=rng.randrange(k) if not multiples else 0
            ops.append((1,l,r,value))
    return make_d(k,values,ops)

def make_tree(rng,n,kind):
    if kind=='chain':edges=[(i,i+1) for i in range(1,n)]
    elif kind=='star':edges=[(1,i) for i in range(2,n+1)]
    elif kind=='binary':edges=[(i//2,i) for i in range(2,n+1)]
    else:edges=[(rng.randint(1,i-1),i) for i in range(2,n+1)]
    permutation=list(range(1,n+1));rng.shuffle(permutation)
    return [(permutation[u-1],permutation[v-1]) for u,v in edges],permutation

def random_e(rng,n,m,q,k,X,kind,mode='all'):
    edges,labels=make_tree(rng,n,kind)
    if kind=='chain':stations=[labels[min(n-1,((i+1)*n)//(k+1))] for i in range(k)]
    elif kind=='star':stations=rng.sample(labels[1:],k)
    else:stations=rng.sample(labels,k)
    plans=[]
    for i in range(m):
        if i%7==0 and plans:s,t=plans[-1]
        elif i%7==1 and plans:t,s=plans[-1]
        elif i%7==2:s,t=rng.choice(edges)
        else:s=rng.randint(1,n);t=rng.randint(1,n-1);t+=t>=s
        plans.append((s,t))
    repairs=edges.copy();rng.shuffle(repairs)
    if mode=='none':repairs=[]
    elif mode=='partial':repairs=repairs[:len(repairs)//2]
    events=[(2,)];cursor=0
    while len(events)<q:
        if cursor<len(repairs) and len(events)%2==1:
            u,v=repairs[cursor];cursor+=1;events.append((1,u,v))
        else:events.append((2,))
    return prepare_e(n,X,edges,stations,plans,events)

def small_cases(position):
    rng=random.Random(SEED+position*100)
    for i in range(40):
        if position==1:yield make_a([rng.randint(1,10**9) for _ in range(rng.randint(1,100))])
        elif position==2:
            tasks=[]
            for j in range(rng.randint(1,10)):
                b=rng.randint(1,50);tasks.append((rng.randint(0,1),b+rng.randint(1,20),rng.randint(1,12),b))
            yield make_b(rng.randint(1,30),tasks)
        elif position==3:yield random_c(rng,rng.randint(1,5),rng.randint(1,80),rng.randint(1,10))
        elif position==4:yield random_d(rng,rng.randint(1,20),rng.randint(10,50),rng.choice([11,13,101]),500)
        else:
            n=rng.randint(2,10);yield random_e(rng,n,rng.randint(1,10),rng.randint(1,20),rng.randint(1,min(n-1,5)),i%2,rng.choice(['chain','star','binary','random']))

def dataset(position):
    rng=random.Random(SEED+position*1000)
    if position==1:
        cases=[[1],[2],[3,7,15,31],[2,9,10,12],[128,255,256],[1,2,4,8,16,32,64,128,256],[2]*100,[1]*100,list(range(1,101)),[rng.randint(1,256) for _ in range(100)],[257,258,1023,1024],[10**9,999999999],[32767,65535,65536],[536854528],[3*(1<<28),1<<29,715827882],[2**i for i in range(30)],[10**9]*100,[715827882]*100,[rng.randint(257,10**9) for _ in range(100)],[1+(1<<29),2+(1<<29),3+(1<<29)]]
        for a in cases:yield make_a(a)
    elif position==2:
        for i in range(16):
            n=[1,2,3,10,40,200][i%6];budget=[1,2,9,100,999,1000][i%6];tasks=[]
            for j in range(n):
                a=rng.randint(1,20);b=rng.randint(1,9999);tasks.append((0,rng.randint(b+1,10000),a,b))
            yield make_b(budget,tasks)
        yield make_b(7,[(1,13,4,10),(1,12,3,8),(0,20,9,10)])
        yield make_b(4,[(1,100,2,40),(1,4,100,3),(0,2,3,1)])
        yield make_b(1,[(1,10000,100,9999),(0,10000,3,9999),(0,5,1,1)])
        tasks=[(rng.randint(0,1),10000,rng.randint(1,100),rng.randint(1,9999)) for _ in range(200)];yield make_b(1000,tasks)
    elif position==3:
        for i in range(8):yield random_c(rng,[1,2,5,100][i%4],100+i*100,10,False)
        special=[('new',1,2),('new',1,3),('new',2,2),('new',2,3),('new',1,2),('delete',1,1),('delete',2,1),('new',2,2),('send',1),('delete',1,1),('delete',2,2),('new',1,5),('send',1),('send',1),('send',1),('send',1),('send',1),('send',1)]
        yield make_c(2,special)
        yield make_c(1,[('new',1,1),('send',1),('send',1),('delete',1,1),('new',1,1),('send',1)])
        for i in range(6):yield random_c(rng,1+i*3,300+i*100,10)
        # End reaches 4e9, then send sum exceeds 32 bits; no giant memory bitmap.
        ops=[('new',1,500000) for _ in range(7999)]+[('send',1)];yield make_c(1,ops)
        yield random_c(rng,100,8000,500000)
        ops=[('new',1,500000),('new',2,500000),('new',1,500000),('delete',2,1),('delete',1,1),('new',2,499999),('new',2,500000),('delete',1,1),('new',1,500000),('send',2)];yield make_c(2,ops)
        yield random_c(rng,100,8000,499999)
    elif position==4:
        yield make_d(11,[0,1,10,11,120],[(2,1,5),(1,1,4,10),(2,1,5),(1,2,5,12),(2,2,5)])
        for i in range(4):yield random_d(rng,[5,20,100,1000][i],[50,100,300,1000][i],[11,13,101,999][i],10**6)
        yield make_d(999999999,[10**12,999999998,0],[(2,1,3),(1,1,3,0),(2,1,1)])
        for i in range(4):yield random_d(rng,[10,100,300,1000][i],[40,100,500,1000][i],[11,999983,999999999,999983][i],10**12)
        yield random_d(rng,3000,2000,11,10**12,True)
        for k in (11,999983,999999999):yield random_d(rng,500000,10000,k,10**12,True)
        yield make_d(11,[120,10,11,22,132],[(1,1,5,10),(1,2,4,12),(2,1,5),(1,1,5,1),(2,3,3),(2,2,5)])
        yield random_d(rng,500,1000,999999999,10**12)
        yield random_d(rng,10000,2000,11,10**12)
        for k in (11,999983,999999999):yield random_d(rng,500000,10000,k,10**12)
    else:
        configurations=[(6,10,10,1,0,'chain','all'),(10,10,10,5,1,'star','all'),(100,100,100,20,0,'random','all'),(100,100,100,1,1,'chain','all'),(80,100,100,20,1,'binary','partial'),(99,100,100,10,0,'star','none'),(100000,100000,200000,1,0,'chain','all'),(100000,100000,200000,20,0,'random','all'),(20000,20000,40000,20,0,'star','all'),(20000,20000,40000,20,0,'binary','partial'),(10000,30000,20000,5,0,'random','all'),(10000,30000,20000,5,0,'chain','none'),(100000,100000,200000,20,1,'chain','all'),(100000,100000,200000,1,1,'star','all'),(100000,100000,200000,20,1,'random','all'),(30000,50000,60000,20,1,'binary','all'),(30000,50000,60000,20,1,'random','partial'),(30000,50000,60000,1,1,'chain','all'),(3000,10000,6000,10,1,'star','none'),(3000,10000,6000,20,1,'random','all')]
        for config in configurations:yield random_e(rng,*config)

def configure_scoring(position,tests):
    if position==4:groups=[('s1','n,m≤1000且R≤10^6',20,5),('s2','n,m≤1000',30,5),('s3','a与v均为k的倍数',20,4),('s4','完整范围',30,6)]
    elif position==5:groups=[('s1','n,m≤10',10,2),('s2','n,m,q≤100',20,4),('s3','完整范围，X=0',30,6),('s4','完整范围，X=0或1',40,8)]
    else:
        if position==2:
            for case in tests:case['checkerType']='FLOAT_ABS_1E_3'
        return tests,[]
    at=0;subtasks=[]
    for key,name,score,count in groups:
        for case in tests[at:at+count]:case.update(score=0,subtaskKey=key)
        at+=count;subtasks.append(dict(key=key,label=name,score=score))
    assert at==len(tests);return tests,subtasks

def extra_assets(position):
    if position==4:return [dict(name='oracle_d.cpp',kind='VALIDATOR',content=(ROOT/'oracle_d.cpp').read_text(encoding='utf-8'))]
    if position==5:return [dict(name='probe_e.py',kind='VALIDATOR',content=(ROOT/'probe_e.py').read_text(encoding='utf-8')),dict(name='oracle.cpp',kind='VALIDATOR',content=(ROOT/'oracle.cpp').read_text(encoding='utf-8')),dict(name='offline-certificates.json',kind='REPORT',content=json.dumps(CERTIFICATES))]
    return []
