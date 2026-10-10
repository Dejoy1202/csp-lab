"""Own 39th CSP datasets. Exact inputs, independent oracles, reproducible seed."""
from collections import deque
from decimal import Decimal
from pathlib import Path
import atexit,hashlib,json,random,re,string,uuid
SEED=2025093905
ROOT=Path(__file__).resolve().parent
ORACLE_DESCRIPTION='Decimal exact circle predicate; direct threshold bitmap matching / set union of window intervals; forward Huffman certificates and prefix-dictionary decoder with chronological table; explicit paths and prefix-diameter LCA; exhaustive daily DP, independent min-cost flow, feasible cheapest-prefix certificates'
PATTERN=['111111111','100100101','100111110','100001100','111111100']
RUNTIME={};CERTIFICATES={};META={}
def certificate(p,text,answer,details):
    key=hashlib.sha256(text.encode()).hexdigest();CERTIFICATES[key]=dict(position=p,answer=answer,**details);return text
def helper(name,text):
    if name not in RUNTIME:
        from sandbox import Sandbox
        from validation_runtime import ValidationRuntime
        sb=Sandbox('csp-lab-sandbox:local','oracle-'+uuid.uuid4().hex)
        binary,diagnostic=sb.compile((ROOT/name).read_text(encoding='utf-8'));assert binary is not None,diagnostic
        RUNTIME[name]=ValidationRuntime(sb,binary,60000,512,4096);atexit.register(RUNTIME[name].close)
    result=RUNTIME[name].run(text);assert result['status']=='OK',result;return result['stdout']
def parse(p,text):
    rows=text.splitlines()
    if p==1:
        n,a=map(int,rows[0].split());assert len(rows)==n+1
        points=[tuple(map(Decimal,row.split())) for row in rows[1:]];assert all(len(t)==2 for t in points);return a,points
    if p==2:
        n,L=map(int,rows[0].split());grid=[list(map(int,row.split())) for row in rows[1:]];assert len(grid)==n and all(len(row)==n for row in grid);return L,grid
    if p==3:
        S,D=map(int,rows[0].split());fixed=[tuple(row.split()) for row in rows[1:S+1]];tree=rows[S+1];N=int(rows[S+2]);ops=[row.split() for row in rows[S+3:]];assert len(ops)==N;return D,fixed,tree,ops
    it=iter(map(int,text.split()));n=next(it);param=next(it);a=[next(it) for _ in range(n)]
    if p==4:
        edges=[(next(it)-1,next(it)-1) for _ in range(n-1)];queries=[(next(it)-1,next(it)-1) for _ in range(param)];data=(a,edges,queries)
    else:data=(param,a,[next(it) for _ in range(n)])
    assert next(it,None) is None;return data
def tree_codes(desc):
    at=0;codes={}
    def read(prefix):
        nonlocal at
        tag=desc[at];at+=1
        if tag=='1':
            c=desc[at];at+=1;assert c not in codes and c in string.ascii_letters+string.digits and 1<=len(prefix)<=8;codes[c]=prefix
        else:assert tag=='0';read(prefix+'0');read(prefix+'1')
    read('');assert at==len(desc);return codes

def field_decode(token,codes):
    if not token.startswith('H'):return token
    if token.startswith('HH'):return token[1:]
    assert re.fullmatch(r'H(?:[0-9a-f]{2}){2,}',token)
    raw=bytes.fromhex(token[1:]);padding=raw[-1];assert 0<=padding<=7
    bits=''.join(f'{x:08b}' for x in raw[:-1]);assert padding==0 or bits[-padding:]=='0'*padding
    bits=bits[:len(bits)-padding];inverse={v:k for k,v in codes.items()};prefix='';out=''
    for bit in bits:
        prefix+=bit
        if prefix in inverse:out+=inverse[prefix];prefix=''
    assert not prefix;return out

def headers(data,validate_only=False):
    D,fixed,desc,ops=data;codes=tree_codes(desc);history=[];out=[];inserts=0;compressed=False
    def entry(index):
        assert 1<=index<=len(fixed)+min(len(history),D)
        return fixed[index-1] if index<=len(fixed) else history[-(index-len(fixed))]
    for op in ops:
        kind,index=map(int,op[:2]);assert kind in (1,2,3)
        if kind==1:assert len(op)==2;k,v=entry(index)
        else:
            assert len(op)==(4 if index==0 else 3)
            tokens=op[2:] if index==0 else op[2:]
            compressed|=any(t.startswith('H') and not t.startswith('HH') for t in tokens)
            if index==0:k=field_decode(op[2],codes)
            else:k=entry(index)[0]
            v=field_decode(op[-1],codes)
            assert all(1<=len(t)<=150 for t in tokens)
        assert all(1<=len(t)<=150 and all(c in string.ascii_letters+string.digits for c in t) for t in (k,v))
        out.append(f'{k}: {v}')
        if kind==2:history.append((k,v));inserts+=1
    return '\n'.join(out)+'\n',dict(inserts=inserts,compressed=compressed,kinds=sorted({int(op[0]) for op in ops}))

def validate(p,text):
    data=parse(p,text)
    if p==1:
        a,points=data;assert 1<=a<=1000 and 1<=len(points)<=1000
        assert all(-a<=v<=a and v*100==int(v*100) for point in points for v in point)
    elif p==2:
        L,g=data;assert L in (256,65536) and 9<=len(g)<=200 and all(0<=v<L for row in g for v in row)
        assert watermark(L,g)
    elif p==3:
        D,fixed,desc,ops=data;assert 1<=D<=120 and 1<=len(fixed)<=64 and 1<=len(ops)<=1000
        assert all(len(t)==2 and all(1<=len(s)<=150 and all(c in string.ascii_letters+string.digits for c in s) for s in t) for t in fixed)
        headers(data,True)
    elif p==4:
        a,edges,queries=data;n=len(a);assert 1<=n<=200000 and 1<=len(queries)<=200000 and sorted(a)==list(range(n))
        parent=list(range(n))
        def find(x):
            while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
            return x
        for u,v in edges:
            assert 0<=u<n and 0<=v<n;u,v=find(u),find(v);assert u!=v;parent[u]=v
        assert len({find(i) for i in range(n)})==1 and all(0<=u<n and 0<=v<n for u,v in queries)
    else:
        m,a,b=data;assert 1<=len(a)<=500000 and 1<=m<=10**18 and all(1<=v<=10**9 for row in (a,b) for v in row)

def watermark(L,g):
    n=len(g);possible=set()
    for i in range(n-4):
        for j in range(n-8):
            whites=[];blacks=[]
            for r,row in enumerate(PATTERN):
                for c,v in enumerate(row):(whites if v=='1' else blacks).append(g[i+r][j+c])
            low=max(blacks)+1;high=min(whites)
            if low<=high:possible.update(range(low,high+1))
    return sorted(possible)
def brute_watermark(L,g):
    n=len(g);out=[]
    for k in range(L):
        bitmap=[''.join('1' if v>=k else '0' for v in row) for row in g]
        if any(all(bitmap[i+r][j:j+9]==PATTERN[r] for r in range(5)) for i in range(n-4) for j in range(n-8)):out.append(k)
    return out

def literal_tree(a,edges,queries):
    n=len(a);g=[[] for _ in a]
    for u,v in edges:g[u].append(v);g[v].append(u)
    out=[]
    for x,y in queries:
        parent={x:-1};queue=deque([x])
        while y not in parent:
            u=queue.popleft()
            for v in g[u]:
                if v not in parent:parent[v]=u;queue.append(v)
        values=set();u=y
        while u!=-1:values.add(a[u]);u=parent[u]
        mex=0
        while mex in values:mex+=1
        out.append(mex)
    return '\n'.join(map(str,out))+'\n'

def schedule_dp(m,a,b):
    # State (unverified balance, completed count); retain exact minimum total cost.
    dp={(0,0):0}
    for ca,cb in zip(a,b):
        nxt={}
        for (balance,count),cost in dp.items():
            for make,check in ((0,0),(1,0),(0,1),(1,1)):
                if balance+make<check:continue
                state=(balance+make-check,count+check);value=cost+ca*make+cb*check
                if value<=m and value<nxt.get(state,10**30):nxt[state]=value
        dp=nxt
    return max(count for (balance,count),cost in dp.items() if balance==0)

def oracle(p,text):
    data=parse(p,text)
    if p==1:
        a,points=data;inside=sum(x*x+y*y<=a*a for x,y in points);return str(Decimal(4)*inside/len(points))+'\n'
    if p==2:
        L,g=data;answer=watermark(L,g)
        if L==256 and len(g)<=20:assert answer==brute_watermark(L,g)
        return '\n'.join(map(str,answer))+'\n'
    if p==3:
        answer,_=headers(data);cert=CERTIFICATES.get(hashlib.sha256(text.encode()).hexdigest())
        if cert:assert cert['answer']==answer
        return answer
    if p==4:
        a,edges,queries=data
        if len(a)<=1000:return literal_tree(*data)
        return helper('oracle_d.cpp',text)
    m,a,b=data
    if len(a)<=25:return str(schedule_dp(*data))+'\n'
    if len(a)<=3000:return helper('oracle_e.cpp',text)
    cert=CERTIFICATES.get(hashlib.sha256(text.encode()).hexdigest());assert cert and cert['kind']=='feasible-independent-cheapest-subsets'
    return cert['answer']

def compare(p,text,actual,expected):
    if p!=1:return actual.split()==expected.split()
    try:return len(actual.split())==1 and Decimal(actual.strip()).is_finite() and abs(Decimal(actual.strip())-Decimal(expected.strip()))<Decimal('0.000000001')
    except Exception:return False

def point_string(v):
    sign='-' if v<0 else '';v=abs(v);return f'{sign}{v//100}.{v%100:02d}'
def make_a(r,n,a,integer=False,boundary=False):
    points=[]
    while len(points)<n:
        x,y=(r.randint(-a,a)*100,r.randint(-a,a)*100) if integer else (r.randint(-100*a,100*a),r.randint(-100*a,100*a))
        if x*x+y*y==(100*a)**2:continue
        points.append((x,y))
    if boundary:points[:min(n,5)]=[(100*a,0),(-100*a,0),(0,100*a),(0,-100*a),(60*a,80*a)][:min(n,5)]
    return f'{n} {a}\n'+''.join(f'{x//100} {y//100}\n' if integer else f'{point_string(x)} {point_string(y)}\n' for x,y in points)

def make_b(r,n,L,index=0):
    g=[[r.randrange(L) for _ in range(n)] for _ in range(n)]
    low,high=(1,L-1) if index==19 else (1+r.randrange(max(1,L//2)),L-1)
    if index%3==0:high=low
    locations=[(0,0)] if n<18 else [(0,0),(n-5,n-9)]
    for q,(top,left) in enumerate(locations):
        lo=low if q==0 else min(L-2,high);hi=high if q==0 else L-1
        for i,row in enumerate(PATTERN):
            for j,v in enumerate(row):g[top+i][left+j]=r.randint(lo,hi) if v=='1' else r.randint(0,lo-1)
        # Certify exact endpoint equality, including low=1 and upper=L-1.
        g[top][left]=hi;g[top+1][left+1]=lo-1
    if index==19:
        for i,row in enumerate(PATTERN):
            for j,v in enumerate(row):g[i][j]=L-1 if v=='1' else 0
    return f'{n} {L}\n'+'\n'.join(' '.join(map(str,row)) for row in g)+'\n'

def make_huffman(chars,skew=False):
    def node(s):
        if len(s)==1:return '1'+s
        cut=1 if skew else len(s)//2;return '0'+node(s[:cut])+node(s[cut:])
    return node(chars)
def encode_field(value,codes,compressed=False):
    if not compressed:return ('H' if value.startswith('H') else '')+value
    bits=''.join(codes[c] for c in value);padding=(-len(bits))%8;bits+='0'*padding
    return 'H'+''.join(f'{int(bits[i:i+8],2):02x}' for i in range(0,len(bits),8))+f'{padding:02x}'
def make_c(r,S,D,N,stage=4,skew=False):
    chars='H0a1bcDxy' if skew else string.ascii_letters+string.digits
    desc=make_huffman(chars,skew);codes=tree_codes(desc);fixed=[('H'+str(i%7),('v'+str(i))*2) for i in range(S)];history=[];ops=[];expected=[];insertions=0
    if stage==1 and S==1:fixed=[('H'*150,'Z'*150)]
    for t in range(N):
        available=S+min(len(history),D)
        def lookup(index):return fixed[index-1] if index<=S else history[-(index-S)]
        if stage==1:kind=1
        elif stage==2:kind=1 if t%3==0 else 3
        elif stage==3:kind=2 if insertions<D and t%3==0 else 1 if t%3==1 else 3
        else:kind=[2,1,3,2,1,2,3][t%7]
        index=available if t%4==0 else r.randint(1,available)
        if kind==1:k,v=lookup(index);op=f'1 {index}'
        else:
            fresh=t%3!=1
            k='H'+('key'+str(t)) if fresh else lookup(index)[0]
            v=('H'*min(149,1+t%149)) if t%9==0 else ''.join(r.choice(chars) for _ in range(1+t%60))
            compressed=stage>=3 and t%2==0
            if compressed and fresh:k=''.join(r.choice(chars) for _ in range(1+t%20))
            vk=encode_field(k,codes,compressed) if fresh else None;vv=encode_field(v,codes,compressed)
            # A raw H-run can be long; keep encoded length <=150 while testing 149 Hs elsewhere.
            if len(vv)>150:v=v[:50];vv=encode_field(v,codes,compressed)
            op=f'{kind} 0 {vk} {vv}' if fresh else f'{kind} {index} {vv}'
        ops.append(op);expected.append(f'{k}: {v}')
        if kind==2:history.append((k,v));insertions+=1
    text=f'{S} {D}\n'+''.join(k+' '+v+'\n' for k,v in fixed)+desc+'\n'+str(N)+'\n'+'\n'.join(ops)+'\n'
    return certificate(3,text,'\n'.join(expected)+'\n',dict(kind='forward-encoded-original-fields',stage=stage,inserts=insertions))

def make_d(r,n,q,shape='random',permutation='random'):
    a=list(range(n))
    if permutation=='random':r.shuffle(a)
    elif permutation=='reverse':a.reverse()
    edges=[]
    for v in range(1,n):edges.append((v-1 if shape=='chain' else 0 if shape=='star' else (v-1)//2 if shape=='binary' else r.randrange(v),v))
    queries=[(0,n-1),(n-1,0),(0,0),(n-1,n-1),(a.index(0),a.index(0))][:q]
    while len(queries)<q:
        if len(queries)%7==0:queries.append((r.randrange(n),n-1))
        else:queries.append((r.randrange(n),r.randrange(n)))
    r.shuffle(edges)
    return f'{n} {q}\n'+' '.join(map(str,a))+'\n'+''.join(f'{u+1} {v+1}\n' for u,v in edges+queries)

def encode_e(m,a,b):return f'{len(a)} {m}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n'
def make_e(r,n,mode='random',budget=None):
    if mode=='random':a=[r.randint(1,10**9) for _ in range(n)];b=[r.randint(1,10**9) for _ in range(n)]
    elif mode=='constant':a=[r.randint(1,10**9)]*n;b=[r.randint(1,10**9)]*n
    elif mode=='front':a=sorted(r.randint(1,10**9) for _ in range(n));b=sorted((r.randint(1,10**9) for _ in range(n)),reverse=True)
    elif mode=='make-constant':a=[7]*n;b=[r.randint(1,10**9) for _ in range(n)]
    elif mode=='check-constant':a=[r.randint(1,10**9) for _ in range(n)];b=[11]*n
    elif mode=='blocks':
        a=([1,10**9]*((n+1)//2))[:n];b=([10**9,1]*((n+1)//2))[:n]
    else:raise ValueError(mode)
    if n<=3000:return encode_e(budget or max(1,(sum(a)+sum(b))*r.randint(1,99)//100),a,b)
    # Independent lower bound: separate cheapest create days and check days.
    # Certify prefix feasibility, so this lower bound is actually attained.
    sa=sorted((v,i) for i,v in enumerate(a));sb=sorted((v,-i) for i,v in enumerate(b));marginals=[x[0]+y[0] for x,y in zip(sa,sb)]
    target=r.randrange(1,n);base=sum(marginals[:target]);m=budget if budget is not None else base+r.randrange(marginals[target]);m=max(1,m)
    total=0;k=0
    for marginal in marginals:
        if total+marginal>m:break
        total+=marginal;k+=1
    balance=[0]*n
    for _,i in sa[:k]:balance[i]+=1
    for _,minus_i in sb[:k]:balance[-minus_i]-=1
    prefix=0
    for change in balance:prefix+=change;assert prefix>=0
    assert prefix==0
    text=encode_e(m,a,b)
    return certificate(5,text,str(k)+'\n',dict(kind='feasible-independent-cheapest-subsets',mode=mode,selected=k,minimumCost=total,nextCost=total+marginals[k] if k<n else None,budget=m))

def small_cases(p):
    r=random.Random(SEED+p)
    for i in range(40):
        if p==1:yield make_a(r,1+i%30,1+i*7,i%2==0,i%3==0)
        elif p==2:yield make_b(r,9+i%7,256,i)
        elif p==3:yield make_c(r,1+i%8,1+i%5,10+i,1+i%4,i%3==0)
        elif p==4:yield make_d(r,1+i%20,1+i*2,['random','chain','star','binary'][i%4],['random','reverse','identity'][i%3])
        else:yield make_e(r,1+i%9,budget=[1,10**18,None][i%3])

def dataset(p):
    r=random.Random(SEED+100*p)
    if p==1:
        for i in range(20):
            if i==0:yield '1 1\n0 0\n'
            elif i==1:yield '1 1\n1 1\n'
            elif i==2:yield '1000 1000\n'+'0 0\n'*1000
            else:yield make_a(r,1000 if i%5==4 else 10+i*7,1000 if i%4==0 else 5+i*13,i<10,i%10>=6)
    elif p==2:
        for i in range(16):yield make_b(r,9+i*2,256,i)
        for i,(n,L) in enumerate([(200,256),(51,65536),(199,65536),(200,65536)],16):yield make_b(r,n,L,i)
    elif p==3:
        for i in range(4):yield make_c(r,[1,64,7,64][i],120,1000,1)
        for i in range(4):yield make_c(r,64,1+i,1000,2)
        for i in range(4):yield make_c(r,64,120,1000,3,i%2==0)
        for i in range(8):yield make_c(r,1+i*9,1 if i==0 else 120 if i%2 else 2+i,1000,4,i%2==0)
    elif p==4:
        for i in range(4):yield make_d(r,[1,9,1000,999][i],1000,['random','star','binary','random'][i])
        for i in range(4):yield make_d(r,200000,200000,'chain',['identity','reverse','random','random'][i])
        for i in range(6):yield make_d(r,50000,50000,['star','binary','random'][i%3])
        for i in range(6):yield make_d(r,200000,200000,['star','binary','random'][i%3])
    else:
        for i in range(4):yield make_e(r,[1,8,99,100][i],budget=[1,10**18,None,None][i])
        for i in range(6):yield make_e(r,3000 if i>=3 else 500+i*500,'random' if i%2 else 'constant')
        for i in range(4):yield make_e(r,100000,['front','make-constant','check-constant','blocks'][i])
        for i in range(6):yield make_e(r,500000,['front','make-constant','check-constant','blocks','constant','front'][i],budget=10**18 if i==5 else None)

def configure_scoring(p,tests):
    if p==1:
        for t in tests:t['checkerType']='FLOAT_ABS_1E_4'
        return tests,[]
    if p==3:return tests,[]
    if p==4:
        for i,t in enumerate(tests):
            a,edges,queries=parse(4,t['input']);n=len(a)
            if i<4:assert n<=1000 and len(queries)<=1000
            if 4<=i<8:
                degree=[0]*n
                for u,v in edges:degree[u]+=1;degree[v]+=1
                assert max(degree)<=2
            if 8<=i<14:assert n<=50000 and len(queries)<=50000
        groups=[('s1','n,m≤1000',20,4),('s2','树为链',20,4),('s3','n,m≤50000',30,6),('s4','完整范围',30,6)]
    elif p==5:
        for i,t in enumerate(tests):
            n=len(parse(5,t['input'])[1]);assert n<=[100,3000,100000,500000][0 if i<4 else 1 if i<10 else 2 if i<14 else 3]
        groups=[('s1','n≤100',20,4),('s2','n≤3000',30,6),('s3','n≤100000',20,4),('s4','完整范围',30,6)]
    else:return tests,[]
    at=0;subtasks=[]
    for key,label,score,count in groups:
        for case in tests[at:at+count]:case.update(score=0,subtaskKey=key)
        at+=count;subtasks.append(dict(key=key,label=label,score=score))
    assert at==len(tests);return tests,subtasks

def extra_assets(p):
    assets=[]
    if p in (3,5):assets.append(dict(name='probe.py',kind='VALIDATOR',content=(ROOT/'probe.py').read_text(encoding='utf-8')))
    if p in (4,5):assets.append(dict(name=f'oracle_{"d" if p==4 else "e"}.cpp',kind='VALIDATOR',content=(ROOT/f'oracle_{"d" if p==4 else "e"}.cpp').read_text(encoding='utf-8')))
    if p in (3,5):assets.append(dict(name='certificates.json',kind='REPORT',content=json.dumps({k:v for k,v in CERTIFICATES.items() if v['position']==p},ensure_ascii=False)))
    return assets
