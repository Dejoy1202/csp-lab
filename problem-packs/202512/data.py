"""Own 202512 data: deterministic, independently checked, no downloaded hidden data."""
from collections import Counter,deque
from functools import lru_cache
from pathlib import Path
import atexit,hashlib,json,random,string,uuid
SEED=2025124005
ROOT=Path(__file__).resolve().parent
ORACLE_DESCRIPTION='Set symmetric difference; algebraic reverse rounds; forward encryption with literal physical-rotation cross-check; seven-tuple enumeration plus ordinary factorization; conflict coloring and weighted bipartite matching'
RUNTIME={};IMAGES={};CERTIFICATES=[]
def helper(name,text):
    if name not in RUNTIME:
        from sandbox import Sandbox
        from validation_runtime import ValidationRuntime
        sandbox=Sandbox('csp-lab-sandbox:local','oracle-'+uuid.uuid4().hex)
        binary,diagnostic=sandbox.compile((ROOT/name).read_text(encoding='utf-8'));assert binary is not None,diagnostic
        RUNTIME[name]=ValidationRuntime(sandbox,binary,60000,1024,4096);atexit.register(RUNTIME[name].close)
    result=RUNTIME[name].run(text);assert result['status']=='OK',result;return result['stdout']
def parse(p,text):
    rows=text.splitlines()
    if p==1:
        it=iter(map(int,text.split()));n,m=next(it),next(it);a=[next(it) for _ in range(n)];s=[];t=[]
        for group in (s,t):
            for _ in range(m):group.append([next(it) for _ in range(next(it))])
        assert next(it,None) is None;return a,s,t
    if p==2:
        it=iter(map(int,text.split()));n,m=next(it),next(it);keys=[next(it) for _ in range(m)];values=[next(it) for _ in range(n)]
        assert next(it,None) is None;return keys,values
    if p==3:
        z=int(rows[0]);image=rows[1:z+1];it=iter(map(int,' '.join(rows[z+1:]).split()));length,t=next(it),next(it)
        ops=[tuple(next(it) for _ in range(6)) for _ in range(t)];assert length==6*t+1 and next(it,None) is None;return image,ops
    if p==4:
        v=list(map(int,text.split()));assert len(v)==2;return tuple(v)
    it=iter(map(int,text.split()));n,W=next(it),next(it);bags=[[next(it) for _ in range(next(it))] for _ in range(n)];q=next(it);ops=[]
    for _ in range(q):
        op=next(it);ops.append((op,next(it),next(it)) if op in (1,2) else (op,))
    assert next(it,None) is None;return W,bags,ops
def validate(p,text):
    data=parse(p,text)
    if p==1:
        a,s,t=data;assert 1<=len(a)<=10000 and 1<=len(s)<=100
        assert all(0<=x<2**31 for x in a)
        for group in (s,t):
            for v in group:assert 1<=len(v)<=1000 and v==sorted(set(v)) and 1<=v[0]<=v[-1]<=len(a)
    elif p==2:
        k,a=data;assert 1<=len(k)<=1000 and 1<=len(a)<=500000 and all(0<=x<8 for x in k) and all(0<=x<512 for x in a)
    elif p==3:
        image,ops=data;z=len(image);assert 1<=z<=400 and 1<=len(ops)<=50000
        assert all(len(row)==z and all(c in string.ascii_letters+string.digits+'_?' for c in row) for row in image)
        for op,u,v,l,d,r in ops:
            if op==1:assert 1<=l<=min(z,10) and 1<=u<=z-l+1 and 1<=v<=z-l+1 and d in (90,180,270) and 0<=r<=3
            else:assert op==2 and 1<=u<=v<=z and 1<=l<=d<=z and v-u+1<=10 and d-l+1<=10 and r in (-1,1)
        origin=IMAGES.get(hashlib.sha256(text.encode()).hexdigest())
        if origin:
            h,w=map(int,origin.splitlines()[0].split());assert 1<=h<=z and 1<=w<=z
            assert all(len(row)==w and '?' not in row for row in origin.splitlines()[1:])
    elif p==4:assert data[0] in (0,1) and 1<=data[1]<=10000000
    else:
        W,bags,ops=data;n=len(bags);assert 1<=n<=500000 and 1<=len(ops)<=500000 and 1<=sum(map(len,bags))<=500000 and 0<W<=2**63-1
        assert all(0<=x<=10**9 for bag in bags for x in bag);active=set(range(1,n+1))
        for event in ops:
            if event[0]==1:assert len(event)==3 and event[1] in active and 0<=event[2]<=10**9
            elif event[0]==2:assert len(event)==3 and event[1]!=event[2] and event[1] in active and event[2] in active;active.remove(event[2])
            else:assert event==(3,)
def sets_answer(a,s,t):
    output=[]
    for left,right in zip(s,t):
        # XOR over the symmetric difference; equivalent hashes without two shared loops.
        different=set(left)^set(right);value=0
        for x in different:value^=a[x-1]
        output.append('correct' if (not different)==(value==0) else 'wrong')
    return '\n'.join(output)+'\n'
def f(x,k):return ((x*x+k*k)%8)^k
def forward(x,k):
    a,b,c=x//64,x//8%8,x%8
    return b*64+(c^f(b,k))*8+(a^f(c,k))
def inverse_round(x,k):
    a1,b1,c1=x//64,x//8%8,x%8
    b=a1;c=b1^f(b,k);a=c1^f(c,k)
    return a*64+b*8+c
def number_answer(keys,values):
    # Algebraic inversion, unlike the C++ forward lookup construction.
    mapping=[]
    for value in range(512):
        x=value
        for key in reversed(keys):x=inverse_round(x,key)
        check=x
        for key in keys:check=forward(check,key)
        assert check==value
        mapping.append(x)
    assert len(set(mapping))==512
    return ' '.join(str(mapping[x]) for x in values)+'\n'
def rotate_cw(a):return [list(row) for row in zip(*a[::-1])]
def physical_encrypt(origin,z,ops):
    a=[list(origin[r]) if r<len(origin) else [] for r in range(z)]
    for row in a:row.extend('?'*(z-len(row)))
    for op,u,v,l,d,r in ops:
        if op==1:
            u-=1;v-=1;b=[row[v:v+l] for row in a[u:u+l]]
            for _ in range(d//90):b=rotate_cw(b)
            for x in range(l):a[u+x][v:v+l]=b[x]
            for _ in range(r):a=[list(row) for row in zip(*a)][::-1]
        else:
            u-=1;v-=1;l-=1;d-=1;b=[row[l:d+1] for row in a[u:v+1]]
            b=b[::-1] if r==1 else [row[::-1] for row in b]
            for x in range(v-u+1):a[u+x][l:d+1]=b[x]
    return [''.join(row) for row in a]
def encrypt(origin,z,ops):
    a=[list(origin[r]) if r<len(origin) else [] for r in range(z)]
    for row in a:row.extend('?'*(z-len(row)))
    turn=0
    def at(r,c):
        if turn==0:return r,c
        if turn==1:return c,z-1-r
        if turn==2:return z-1-r,z-1-c
        return z-1-c,r
    def read(r,c):x,y=at(r,c);return a[x][y]
    def write(r,c,value):x,y=at(r,c);a[x][y]=value
    for op,u,v,L,d,r in ops:
        if op==1:
            u-=1;v-=1;b=[[read(u+x,v+y) for y in range(L)] for x in range(L)]
            for _ in range(d//90):b=rotate_cw(b)
            for x in range(L):
                for y in range(L):write(u+x,v+y,b[x][y])
            turn=(turn+r)%4
        else:
            u-=1;v-=1;L-=1;d-=1;b=[[read(x,y) for y in range(L,d+1)] for x in range(u,v+1)]
            b=b[::-1] if r==1 else [row[::-1] for row in b]
            for x in range(u,v+1):
                for y in range(L,d+1):write(x,y,b[x-u][y-L])
    result=[''.join(read(r,c) for c in range(z)) for r in range(z)]
    if z<=10 or (z<=60 and len(ops)<=400):assert result==physical_encrypt(origin,z,ops)
    return result
def image_input(origin,z,ops):
    image=encrypt(origin,z,ops);text=str(z)+'\n'+'\n'.join(image)+'\n'+str(6*len(ops)+1)+'\n'+str(len(ops))+' '+' '.join(str(v) for op in ops for v in op)+'\n'
    answer=f'{len(origin)} {len(origin[0])}\n'+'\n'.join(origin)+'\n';key=hashlib.sha256(text.encode()).hexdigest();IMAGES[key]=answer
    CERTIFICATES.append(dict(inputSha256=key,originSha256=hashlib.sha256(answer.encode()).hexdigest(),physicalCrossCheck=z<=10 or (z<=60 and len(ops)<=400)))
    return text
def decode_literal(image,ops):
    a=[list(row) for row in image]
    for op,u,v,L,d,r in reversed(ops):
        if op==1:
            for _ in range(r):a=rotate_cw(a)
            u-=1;v-=1;b=[row[v:v+L] for row in a[u:u+L]]
            for _ in range((4-d//90)%4):b=rotate_cw(b)
            for x in range(L):a[u+x][v:v+L]=b[x]
        else:
            u-=1;v-=1;L-=1;d-=1;b=[row[L:d+1] for row in a[u:v+1]]
            b=b[::-1] if r==1 else [row[::-1] for row in b]
            for x in range(v-u+1):a[u+x][L:d+1]=b[x]
    h=max(r+1 for r,row in enumerate(a) for c in row if c!='?');w=max(c+1 for row in a for c,x in enumerate(row) if x!='?')
    assert all((a[r][c]!='?')==(r<h and c<w) for r in range(len(a)) for c in range(len(a)))
    return f'{h} {w}\n'+'\n'.join(''.join(row[:w]) for row in a[:h])+'\n'
@lru_cache(None)
def literal_d(op,n):
    total=0
    for b in range(1,n+1):
        divisors=[c for c in range(1,b*b+1) if b*b%c==0]
        for c in divisors:
            for e in divisors:
                if b**3%(c*e):continue
                a=b*b//c;g=b*b//e;d=b**3//(c*e)
                if not op or len({a,b,c,d,e,b,g})==6:total+=d
    return total%998244353
def flow_cost(items,W):
    if not items:return 0
    if W>=2**30:return sum(items.values())
    h=W.bit_length()-1;groups={}
    for x,c in items.items():groups.setdefault(x>>(h+1),{})[x]=c
    answer=0
    for counts in groups.values():
        total=sum(counts.values())
        if W&(W-1)==0:cost=max(sum(c for x,c in counts.items() if x>>h&1==0),sum(c for x,c in counts.items() if x>>h&1))
        elif W==2**(h+1)-1:
            match=sum(min(c,counts.get(x^W,0)) for x,c in counts.items() if x>>h&1==0);cost=total-match
        else:
            left=[(x,c) for x,c in counts.items() if x>>h&1==0];right=[(x,c) for x,c in counts.items() if x>>h&1]
            N=len(left)+len(right)+2;source=N-2;sink=N-1;graph=[[] for _ in range(N)]
            def edge(a,b,c):
                graph[a].append([b,c,len(graph[b])]);graph[b].append([a,0,len(graph[a])-1])
            for i,(x,c) in enumerate(left):edge(source,i,c)
            for j,(y,c) in enumerate(right):edge(len(left)+j,sink,c)
            for i,(x,c) in enumerate(left):
                for j,(y,d) in enumerate(right):
                    if x^y>=W:edge(i,len(left)+j,total)
            match=0
            while True:
                level=[-1]*N;level[source]=0;queue=deque([source])
                while queue:
                    u=queue.popleft()
                    for v,c,_ in graph[u]:
                        if c and level[v]<0:level[v]=level[u]+1;queue.append(v)
                if level[sink]<0:break
                at=[0]*N
                def dfs(u,cap):
                    if u==sink:return cap
                    while at[u]<len(graph[u]):
                        v,c,rev=graph[u][at[u]]
                        if c and level[v]==level[u]+1:
                            used=dfs(v,min(cap,c))
                            if used:graph[u][at[u]][1]-=used;graph[v][rev][1]+=used;return used
                        at[u]+=1
                    return 0
                while True:
                    used=dfs(source,total)
                    if not used:break
                    match+=used
            cost=total-match
        answer=max(answer,cost)
    return answer
@lru_cache(None)
def brute_colors(values,W):
    if not values:return 0
    # Independent stable-subset partition DP; each duplicate remains a distinct vertex.
    N=len(values);stable=[True]*(1<<N);dp=[N]*(1<<N);dp[0]=0
    for mask in range(1,1<<N):
        bit=mask&-mask;i=bit.bit_length()-1;rest=mask^bit;stable[mask]=stable[rest] and all((values[i]^values[j])>=W for j in range(N) if rest>>j&1)
        sub=mask
        while sub:
            if sub&bit and stable[sub]:dp[mask]=min(dp[mask],dp[mask^sub]+1)
            sub=(sub-1)&mask
    return dp[-1]
def packets_answer(W,original,ops):
    bags=[Counter(b) for b in original];dirty=set(range(len(bags)));cost=[0]*len(bags);out=[]
    for event in ops:
        if event[0]==1:u=event[1]-1;bags[u][event[2]]+=1;dirty.add(u)
        elif event[0]==2:
            u,v=event[1]-1,event[2]-1
            if len(bags[u])<len(bags[v]):bags[u],bags[v]=bags[v],bags[u]
            bags[u].update(bags[v]);bags[v]=Counter();cost[v]=0;dirty.discard(v);dirty.add(u)
        else:
            for u in dirty:
                cost[u]=flow_cost(bags[u],W)
                if sum(bags[u].values())<=10:
                    values=tuple(x for x,c in bags[u].items() for _ in range(c));assert cost[u]==brute_colors(values,W)
            dirty.clear();out.append(sum(cost))
    return '\n'.join(map(str,out))+'\n'
def oracle(p,text):
    data=parse(p,text)
    if p==1:return sets_answer(*data)
    if p==2:return number_answer(*data)
    if p==3:
        key=hashlib.sha256(text.encode()).hexdigest();answer=IMAGES.get(key)
        if answer:
            if len(data[0])<=60 and len(data[1])<=400:assert answer==decode_literal(*data)
            return answer
        return decode_literal(*data)
    if p==4:
        op,n=data
        if n<=100:return str(literal_d(op,n))+'\n'
        return helper('oracle_d.cpp',text)
    return packets_answer(*data)
def encode_a(a,s,t):
    return f'{len(a)} {len(s)}\n'+' '.join(map(str,a))+'\n'+''.join(str(len(v))+' '+' '.join(map(str,v))+'\n' for group in (s,t) for v in group)
def make_a(r,n,m,different=False):
    a=[r.randrange(2**31) for _ in range(n)];a[:3]=[1,2,3];s=[];t=[]
    for j in range(m):
        if j==0:left,right=[1],[2,3]
        elif j==1 and not different:left,right=[1,2],[2,3]
        elif j==2 and not different:left=right=[1,3]
        else:
            left=sorted(r.sample(range(1,n+1),r.randint(1,min(1000,n-1))))
            right=sorted(r.sample(range(1,n+1),r.randint(1,min(1000,n))))
            if different and len(left)==len(right):right=right+[next(x for x in range(1,n+1) if x not in right)] if len(right)<n else right[:-1];right.sort()
        s.append(left);t.append(right)
    return encode_a(a,s,t)
def make_b(r,n,m):
    keys=[r.randrange(8) for _ in range(m)];values=[i%512 if i<512 else r.randrange(512) for i in range(n)]
    return f'{n} {m}\n'+' '.join(map(str,keys))+'\n'+' '.join(map(str,values))+'\n'
def make_c(r,z,t,flip=False,shape=None):
    h,w=shape or (r.randint(1,z),r.randint(1,z));alphabet=string.ascii_letters+string.digits+'_'
    origin=[''.join(alphabet[(i*w+j+r.randrange(63))%63] for j in range(w)) for i in range(h)];ops=[]
    for i in range(t):
        if flip or i%3==0:
            hh,ww=r.randint(1,min(10,z)),r.randint(1,min(10,z));u,l=r.randint(1,z-hh+1),r.randint(1,z-ww+1);ops.append((2,u,u+hh-1,l,l+ww-1,(-1,1)[i%2]))
        else:
            L=r.randint(1,min(10,z));u,v=r.randint(1,z-L+1),r.randint(1,z-L+1);ops.append((1,u,v,L,(90,180,270)[i%3],i%4))
    return image_input(origin,z,ops)
def encode_e(W,bags,ops):
    return f'{len(bags)} {W}\n'+''.join(str(len(b))+' '+ ' '.join(map(str,b))+'\n' for b in bags)+str(len(ops))+'\n'+''.join(' '.join(map(str,op))+'\n' for op in ops)
def make_e(r,n,total,q,upper=1000,W=None,domain=None,mode='mixed'):
    W=W or r.randint(1,upper+2)
    pick=(lambda:r.choice(domain)) if domain else (lambda:r.randint(0,upper))
    bags=[[] for _ in range(n)]
    for i in range(total):bags[i%n].append(pick())
    ops=[];active=list(range(1,n+1))
    if mode=='merge':
        # Balanced merges also exercise swapping roots / arbitrary surviving packet IDs.
        while len(active)>1 and len(ops)<q-1:
            next_active=[]
            for i in range(0,len(active)-1,2):
                u,v=active[i:i+2]
                if r.randrange(2):u,v=v,u
                ops.append((2,u,v));next_active.append(u)
            if len(active)%2:next_active.append(active[-1])
            active=next_active
        while len(ops)<q-1:ops.append((1,active[0],pick()))
        ops.append((3,))
    else:
        checkpoints={0,q//3,2*q//3,q-1}
        for i in range(q):
            if i in checkpoints:ops.append((3,))
            elif n<=1000 and len(active)>1 and i%11==0:
                at=r.randrange(len(active));v=active.pop(at);u=r.choice(active);ops.append((2,u,v))
            else:ops.append((1,r.choice(active),pick()))
    return encode_e(W,bags,ops)
def small_cases(p):
    r=random.Random(SEED+p)
    for i in range(40):
        if p==1:yield make_a(r,r.randint(3,12),r.randint(3,8),i%2==0)
        elif p==2:yield make_b(r,r.randint(1,30),r.randint(1,15))
        elif p==3:yield make_c(r,r.randint(1,10),r.randint(1,40),i%4==0)
        elif p==4:yield f'{i%2} {i//2+1}\n'
        else:yield make_e(r,r.randint(1,5),r.randint(1,7),r.randint(1,5),15,W=r.choice([1,2,3,5,7,8,9,15,16,17,32]))
def dataset(p):
    r=random.Random(SEED+100*p)
    if p==1:
        for i in range(20):
            if i==10:yield encode_a([0],[[1]],[[1]])
            elif i==11:yield encode_a([0]*3,[[1],[1,3],[1,2]],[[2],[2,3],[1,2]])
            elif i==12:yield encode_a([0,2**31-1,2**31-1],[[2],[1,2],[1,3]],[[3],[2],[1,3]])
            else:
                text=make_a(r,10000 if i in (9,19) else 3+i*5,100 if i in (9,19) else 4+i,i<10)
                if i==19:
                    a,s,t=parse(1,text);s[0]=list(range(1,1001));t[0]=list(range(9001,10001));text=encode_a(a,s,t)
                yield text
    elif p==2:
        for i in range(16):yield make_b(r,1+i*6,1+i%20)
        for n,m in [(512,1000),(500000,1),(500000,1000),(499999,999)]:yield make_b(r,n,m)
    elif p==3:
        for i in range(5):yield make_c(r,1+i*2,1+i*15,True,shape=(1+i,1))
        for z,t in [(11,3),(37,200),(400,50000),(399,49999),(400,10000)]:yield make_c(r,z,t,True)
        for i in range(5):yield make_c(r,2+i*2,5+i*40,False,shape=(1,2+i))
        for z,t,shape in [(40,200,(39,40)),(400,50000,(400,400)),(400,50000,(1,400)),(399,49999,(399,1)),(400,10000,(313,271))]:yield make_c(r,z,t,False,shape=shape)
    elif p==4:
        for op,n in [(0,1),(1,1),(0,2),(1,4),(0,10),(1,10),(0,97),(0,1000),(0,99991),(0,100000),(1,97),(1,1000),(1,65536),(1,100000),(0,9999991),(0,10000000),(0,8388608),(1,9999991),(1,10000000),(1,8388608)]:yield f'{op} {n}\n'
    else:
        for n,total,q,W in [(1,1,1,1),(3,6,10,3),(4,8,10,15),(10,10,10,1024)]:yield make_e(r,n,total,q,W=W)
        for W in (1,513,1001):yield make_e(r,100,100,100,W=W)
        for W in (65537,524287,999999):yield make_e(r,1000,1000,1000,10**6,W=W,domain=[0,1,7,65536,65537,524287,999999])
        for W in (1,65536,524287,777777):yield make_e(r,1000,100000,100000,10**6,W=W,domain=[0,1,7,65536,65537,524287,999999])
        yield make_e(r,500000,500000,500000,10**9,W=1<<20,mode='merge')
        yield make_e(r,1,500000,500000,W=45,domain=list(range(64)))
        yield make_e(r,250000,1,500000,10**9,W=1<<16,mode='merge')
        scattered=[sum(((x>>j)&1)<<b for j,b in enumerate([0,3,7,13,18,22,26,29])) for x in range(256)]
        yield make_e(r,8,500000,500000,10**9,W=500000003,domain=scattered)
        yield make_e(r,4,500000,100000,10**9,W=(1<<29)-1,domain=[x for v in range(128) for x in (v,v^((1<<29)-1))])
        yield make_e(r,500000,500000,500000,10**9,W=2**40,mode='merge')
def configure_scoring(p,tests):
    if p==3:groups=[('s1','仅翻转，Z≤10',25,5),('s2','仅翻转，完整Z范围',25,5),('s3','Z≤10，含旋转',25,5),('s4','完整范围',25,5)]
    elif p==4:groups=[('s1','op=0或1，n≤10',30,6),('s2','op=0，n≤10⁵',20,4),('s3','op=0或1，n≤10⁵',30,4),('s4','op=0，n≤10⁷',10,3),('s5','完整范围',10,3)]
    elif p==5:groups=[('s1','n,q及初始元素总数≤10，权值≤10³',20,4),('s2','规模≤100，权值≤10³',15,3),('s3','规模≤10³，权值≤10⁶',15,3),('s4','规模≤10^5，权值≤10⁶',20,4),('s5','完整范围',30,6)]
    else:return tests,[]
    at=0;subtasks=[]
    for key,label,score,count in groups:
        for case in tests[at:at+count]:case.update(score=0,subtaskKey=key)
        at+=count;subtasks.append(dict(key=key,label=label,score=score))
    assert at==len(tests);return tests,subtasks
def extra_assets(p):
    if p==3:return [dict(name='probe.py',kind='VALIDATOR',content=(ROOT/'probe.py').read_text(encoding='utf-8')),dict(name='image-certificates.json',kind='REPORT',content=json.dumps(CERTIFICATES))]
    if p==4:return [dict(name='probe.py',kind='VALIDATOR',content=(ROOT/'probe.py').read_text(encoding='utf-8')),dict(name='oracle_d.cpp',kind='VALIDATOR',content=(ROOT/'oracle_d.cpp').read_text(encoding='utf-8'))]
    if p==5:return [dict(name='probe.py',kind='VALIDATOR',content=(ROOT/'probe.py').read_text(encoding='utf-8'))]
    return []
