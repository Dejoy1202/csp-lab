"""Original generated fixtures and independent boundary oracles for CSP43."""
from collections import deque,Counter
from decimal import Decimal,localcontext,ROUND_HALF_UP
from itertools import combinations
from functools import lru_cache
import bisect
import math
import random
import re
from checkers import check_output
SEED=2026094301
ORACLE_DESCRIPTION='High-precision decimal nearest lookup; exhaustive subsets and weight DP; millisecond scheduler; explicit small graph bipartiteness plus certified large families; path enumeration and independent star/chain/monochrome counting'

@lru_cache(maxsize=1001)
def cdf_text(value):
    # Independent integration series, rather than the generator's math.erf.
    with localcontext() as ctx:
        ctx.prec=80
        x=Decimal(value);term=x;area=x
        for j in range(100):
            term *= -x*x*Decimal(2*j+1)/(Decimal(2)*(j+1)*(2*j+3))
            area += term
            if abs(term)<Decimal('1e-70'):break
        pi=Decimal('3.14159265358979323846264338327950288419716939937510582097494459230781640628620899')
        probability=Decimal('.5')+area/(2*pi).sqrt()
        return format(probability.quantize(Decimal('.001'),rounding=ROUND_HALF_UP),'.3f')

def parse(position,text):
    rows=text.splitlines()
    if position==1:
        n,m,k=map(int,rows[0].split());return n,m,k,rows[1].split(),rows[2].split(),rows[3].split(),rows[4].split()
    if position==2:
        n,m,q=rows[0].split();return int(n),int(m),int(q.replace('.','')),list(map(int,rows[1].split())),[int(s.replace('.','')) for s in rows[2].split()]
    if position==3:
        n,m,T=map(int,rows[0].split());return n,m,T,list(map(int,rows[1].split())),[list(map(int,r.split())) for r in rows[2:]]
    if position==4:
        n,k,op=map(int,rows[0].split());return n,k,op,list(map(int,rows[1].split()))
    n,m,k,q=map(int,rows[0].split());return n,m,k,q,rows[1],list(map(int,rows[2].split())),[tuple(map(int,r.split())) for r in rows[3:n+2]],[int(r) for r in rows[n+2:]]

def validate(position,text):
    assert text.endswith('\n')
    item=parse(position,text)
    if position==1:
        n,m,k,mu,sigma,x,phi=item
        assert 1<=n<=100 and 1<=m<=100 and 2<=k<=20 and len(mu)==len(sigma)==n and len(x)==len(phi)==k
        assert all(re.fullmatch(r'[0-9]+\.[0-9]{3}',s) for s in mu+sigma+x+phi)
        assert phi==[cdf_text(s) for s in x], 'Table must contain rounded standard normal CDF values'
        mu,sigma,x,phi=[[Decimal(s) for s in a] for a in (mu,sigma,x,phi)]
        assert all(0<s<=100 for s in mu) and all(0<s<=10 for s in sigma)
        assert 0<=x[0]<x[-1]<=1 and all(a<b for a,b in zip(x,x[1:]))
        assert Decimal('.500')<=phi[0]<phi[-1]<=Decimal('.841') and all(a<b for a,b in zip(phi,phi[1:]))
        with localcontext() as ctx:
            ctx.prec=60;z=(Decimal(m)-sum(mu))/sum(s*s for s in sigma).sqrt()
            assert x[0]<=z<=x[-1]
    elif position==2:
        n,m,q,mu,sigma=item
        assert 1<=n<=100 and 1<=m<=10 and 500<=q<=1000 and len(mu)==len(sigma)==n
        assert re.fullmatch(r'[01]\.[0-9]{3}',text.split()[2])
        assert all(1<=v<=100 for v in mu) and all(1<=s<=30 for s in sigma)
        assert all(re.fullmatch(r'[0-3]\.[0-9]',s) for s in text.splitlines()[2].split())
    elif position==3:
        n,m,T,taskslice,tasks=item
        assert 1<=n<=100 and 1<=m<=100 and 1<=T<=10**9 and len(taskslice)==m and len(tasks)==n
        assert all(1<=t<=100 for t in taskslice)
        for work,count,*preferences in tasks:
            assert 1<=work<=100 and 0<=count<=m and len(preferences)==len(set(preferences))==count and all(1<=p<=m for p in preferences)
    elif position==4:
        n,k,op,values=item
        assert 1<=n<=500000 and 2<=k<=10**9 and op in (0,1) and len(values)==len(set(values))==n
        assert all(1<=x<=10**18 for x in values)
    else:
        n,m,k,q,state,colors,edges,toggles=item
        assert 1<=n<=100000 and 1<=m<=40 and 1<=k<=4 and 0<=q<=100000
        assert len(state)==n and set(state)<={'0','1'} and len(colors)==n and all(1<=c<=m for c in colors)
        assert len(edges)==n-1 and len(toggles)==q and all(1<=u<=n for u in toggles)
        parents=list(range(n))
        def root(v):
            while parents[v]!=v:parents[v]=parents[parents[v]];v=parents[v]
            return v
        for u,v,w in edges:
            assert 1<=u<=n and 1<=v<=n and 1<=w<=10**6
            a,b=root(u-1),root(v-1);assert a!=b;parents[a]=b

def lookup(item):
    n,m,k,mu,sigma,x,phi=item
    with localcontext() as ctx:
        ctx.prec=60;z=(Decimal(m)-sum(map(Decimal,mu)))/sum(Decimal(s)**2 for s in sigma).sqrt()
        chosen=min(range(k),key=lambda i:(abs(Decimal(x[i])-z),Decimal(x[i])))
    return phi[chosen]+'\n'

def knapsack(item):
    n,m,q,mu,sigma=item;weight=[s*s for s in sigma];limit=(m*10000)**2//(q*q)
    if n<=16:
        best=0
        for mask in range(1<<n):
            w=sum(weight[i] for i in range(n) if mask>>i&1)
            if w<=limit:best=max(best,sum(mu[i] for i in range(n) if mask>>i&1))
        return str(best)+'\n'
    limit=min(limit,sum(weight));dp=[-1]*(limit+1);dp[0]=0
    for w,v in zip(weight,mu):
        for capacity in range(limit,w-1,-1):
            if dp[capacity-w]>=0:dp[capacity]=max(dp[capacity],dp[capacity-w]+v)
    return str(max(dp))+'\n'

def schedule(item):
    n,m,T,slices,tasks=item;remaining=[r[0] for r in tasks];preferred=[set(r[2:]) for r in tasks]
    queues=[deque() for _ in range(m)]
    for i in range(n):queues[i%m].append(i)
    running=[None]*m;finish=[0]*m;first=[None]*n;answer=[0]*n;now=0;done=0
    while done<n:
        # Iterate every millisecond, unlike the C++ event-based implementation.
        before=max(0,(now-1)//T)
        for cpu in range(m):
            if running[cpu] is not None and finish[cpu]==now:
                task=running[cpu];running[cpu]=None
                if remaining[task]:queues[(cpu+before)%m].append(task)
                else:answer[task]=now-first[task];done+=1
        rotation=now//T
        for cpu in range(m):
            queue=queues[(cpu+rotation)%m]
            if running[cpu] is None and queue:
                task=queue.popleft();running[cpu]=task
                if first[task] is None:first[task]=now
                speed=2 if cpu+1 in preferred[task] else 1
                duration=min(slices[cpu],(remaining[task]+speed-1)//speed)
                remaining[task]=max(0,remaining[task]-duration*speed);finish[cpu]=now+duration
        now+=1
        assert now<=10001
    return ' '.join(map(str,answer))+'\n'

def groups_minimum(item):
    n,k,op,values=item;values=sorted(values);members=set(values)
    if op==0:return 2 if any(x*k in members for x in values) else 1
    if n>2000:
        if values[-1]<k*values[0]:return 1
        # A present 5-cycle proves at least 3; the universal level mod3 construction proves at most 3.
        if k==2 and {4,8,16,11,32}<=members:return 3
        # k greater than all low values: exact matching pairs with no other cross edges.
        if k==10**9 and n==500000 and values[:250000]==list(range(1,250001)) and values[250000:]==[k*x for x in range(1,250001)]:return 2
        raise AssertionError('Large construction fixture needs a certified optimum')
    graph=[[] for _ in range(n)];edge=False
    for i,x in enumerate(values):
        lo=bisect.bisect_left(values,k*x);hi=bisect.bisect_left(values,(k+1)*x)
        for j in range(lo,hi):graph[i].append(j);graph[j].append(i);edge=True
    if not edge:return 1
    color=[-1]*n
    for start in range(n):
        if color[start]>=0:continue
        color[start]=0;todo=deque([start])
        while todo:
            u=todo.popleft()
            for v in graph[u]:
                if color[v]<0:color[v]=color[u]^1;todo.append(v)
                elif color[v]==color[u]:return 3
    return 2

def tree_graph(n,edges):
    graph=[[] for _ in range(n)]
    for u,v,w in edges:graph[u-1].append((v-1,w));graph[v-1].append((u-1,w))
    return graph

def tree_small(item):
    n,m,k,q,state,colors,edges,toggles=item;graph=tree_graph(n,edges);eligible=[]
    for start in range(n):
        mask=0;todo=[(start,-1,1<<(colors[start]-1),0)]
        while todo:
            u,parent,parity,residue=todo.pop()
            if residue==0 and parity.bit_count()==1:mask|=1<<u
            for v,w in graph[u]:
                if v!=parent:todo.append((v,u,parity^(1<<(colors[v]-1)),(residue+w)%k))
        eligible.append(mask)
    active=sum(1<<i for i,s in enumerate(state) if s=='1')
    total=(sum((eligible[i]&active).bit_count() for i in range(n) if active>>i&1)+active.bit_count())//2;answer=[total]
    for u in toggles:
        u-=1;count=(eligible[u]&active).bit_count()
        total=total-count if active>>u&1 else total+count+1;active^=1<<u;answer.append(total)
    return '\n'.join(map(str,answer))+'\n'

def tree_monochrome(item,graph):
    n,m,k,q,state,colors,edges,toggles=item
    assert len(set(colors))==1 and all(w%k==0 for _,_,w in edges)
    parity=[0]*n;todo=[(0,-1)]
    for u,parent in todo:
        for v,w in graph[u]:
            if v!=parent:parity[v]=parity[u]^1;todo.append((v,u))
    counts=[0,0];active=[s=='1' for s in state]
    for i in range(n):counts[parity[i]]+=active[i]
    total=sum(c*(c+1)//2 for c in counts);answer=[total]
    for u in toggles:
        u-=1;p=parity[u]
        if active[u]:total-=counts[p];counts[p]-=1
        else:counts[p]+=1;total+=counts[p]
        active[u]=not active[u];answer.append(total)
    return '\n'.join(map(str,answer))+'\n'

def tree_star(item,graph,root):
    n,m,k,q,state,colors,edges,toggles=item;res=[0]*n
    for u,w in graph[root]:res[u]=w%k
    active=[s=='1' for s in state];counts=[[0]*k for _ in range(m)]
    for i in range(n):
        if i!=root and active[i]:counts[colors[i]-1][res[i]]+=1
    def pairs(u):
        want=(-res[u])%k;c=colors[u]-1;r=colors[root]-1
        result=sum(counts[j][want] for j in range(m) if c==j or c==r or j==r)
        if active[u] and want==res[u]:result-=1
        return result
    total=sum(active)+(sum(pairs(i) for i in range(n) if i!=root and active[i])//2);answer=[total]
    for u in toggles:
        u-=1;delta=-1 if active[u] else 1
        total+=delta*(1 if u==root else pairs(u)+1)
        if u!=root:counts[colors[u]-1][res[u]]+=delta
        active[u]=not active[u];answer.append(total)
    return '\n'.join(map(str,answer))+'\n'

class IndexedCounts:
    def __init__(self,positions):self.positions=positions;self.bit=[0]*(len(positions)+1)
    def add(self,position,delta):
        i=bisect.bisect_left(self.positions,position)+1
        while i<len(self.bit):self.bit[i]+=delta;i+=i&-i
    def first(self,length):
        value=0
        while length:value+=self.bit[length];length-=length&-length
        return value
    def before(self,position):return self.first(bisect.bisect_left(self.positions,position))
    def after(self,position):return self.first(len(self.positions))-self.first(bisect.bisect_right(self.positions,position))

def tree_chain(item,graph):
    n,m,k,q,state,colors,edges,toggles=item;start=next(i for i,g in enumerate(graph) if len(g)==1)
    order=[];distance=[];previous=-1;now=start;res=0
    while now!=-1:
        order.append(now);distance.append(res);neighbors=[(v,w) for v,w in graph[now] if v!=previous]
        previous,now=now,(neighbors[0][0] if neighbors else -1)
        if neighbors:res=(res+neighbors[0][1])%k
    index=[0]*n;prefix=0;leftKeys=[];rightKeys=[];leftPos={};rightPos={}
    for i,u in enumerate(order):
        index[u]=i;left=(prefix,distance[i]);prefix^=1<<(colors[u]-1);right=(prefix,distance[i])
        leftKeys.append(left);rightKeys.append(right);leftPos.setdefault(left,[]).append(i);rightPos.setdefault(right,[]).append(i)
    left={key:IndexedCounts(p) for key,p in leftPos.items()};right={key:IndexedCounts(p) for key,p in rightPos.items()};active=[False]*n
    def pairs(i):
        value=0;res=distance[i]
        for c in range(m):
            bucket=left.get((rightKeys[i][0]^(1<<c),res))
            if bucket:value+=bucket.before(i)
            bucket=right.get((leftKeys[i][0]^(1<<c),res))
            if bucket:value+=bucket.after(i)
        return value
    def change(i,delta):left[leftKeys[i]].add(i,delta);right[rightKeys[i]].add(i,delta)
    total=0
    for i,u in enumerate(order):
        if state[u]=='1':total+=pairs(i)+1;change(i,1);active[i]=True
    answer=[total]
    for u in toggles:
        i=index[u-1];delta=-1 if active[i] else 1;total+=delta*(pairs(i)+1);change(i,delta);active[i]=not active[i];answer.append(total)
    return '\n'.join(map(str,answer))+'\n'

def tree_oracle(item):
    n,m,k,q,state,colors,edges,toggles=item
    if n<=2000:
        result=tree_small(item)
        if n<=30:
            graph=tree_graph(n,edges)
            if len(set(colors))==1 and all(w%k==0 for _,_,w in edges):assert tree_monochrome(item,graph)==result
            root=next((i for i,g in enumerate(graph) if len(g)==n-1),None)
            if root is not None:assert tree_star(item,graph,root)==result
            if n>1 and all(len(g)<=2 for g in graph):assert tree_chain(item,graph)==result
        return result
    graph=tree_graph(n,edges)
    if len(set(colors))==1 and all(w%k==0 for _,_,w in edges):return tree_monochrome(item,graph)
    root=next((i for i,g in enumerate(graph) if len(g)==n-1),None)
    if root is not None:return tree_star(item,graph,root)
    if all(len(g)<=2 for g in graph):return tree_chain(item,graph)
    raise AssertionError('Large tree fixture needs independent answer model')

def oracle(position,text):
    item=parse(position,text)
    if position==1:return lookup(item)
    if position==2:return knapsack(item)
    if position==3:return schedule(item)
    if position==4:return str(groups_minimum(item))+'\n'
    return tree_oracle(item)

def compare(position,data,output,answer):
    if position==4:return check_output('CSP_GROUP_PARTITION',data,answer,output.encode('utf-8'))
    return output.split()==answer.split()

def configure_scoring(position,cases):
    if position==5 and len(cases)>20:
        assert len(cases)==25
        # Preserve all twenty existing inputs and their 100-point total.
        # The old final 5-point check now also requires the added edge cases.
        tests=[dict(c,score=5,subtaskKey=None) for c in cases[:19]]
        tests += [dict(c,score=0,subtaskKey='initial-state') for c in cases[19:]]
        return tests,[dict(key='initial-state',label='完整规模及初始状态',score=5)]
    if position!=4:return cases,[]
    scores=[10,20,25,20,25];sizes=[2,4,5,4,5];tests=[];groups=[];offset=0
    for number,(score,size) in enumerate(zip(scores,sizes),1):
        for suffix,kind,portion,label in [('count','CSP_GROUP_COUNT',score*2//5,'最少组数'),('plan','CSP_GROUP_PARTITION',score*3//5,'合法划分')]:
            key=f's{number}-{suffix}';groups.append(dict(key=key,label=f'规模档{number}：{label}',score=portion))
            for case in cases[offset:offset+size]:tests.append(dict(case,score=0,subtaskKey=key,checkerType=kind))
        offset+=size
    assert offset==20 and len(cases) in (20,22) and len(tests)==40
    for case in cases[20:]:
        for kind,key in [('CSP_GROUP_COUNT','s1-count'),('CSP_GROUP_PARTITION','s1-plan')]:
            tests.append(dict(case,score=0,subtaskKey=key,checkerType=kind))
    return tests,groups


def thousand(v):return f'{v//1000}.{v%1000:03d}'
def tenth(v):return f'{v//10}.{v%10}'
def normal_case(mu,sigma,m,x=None):
    x=x or list(range(0,1001,50))[:19]+[1000]
    phi=[f'{(1+math.erf(v/1000/math.sqrt(2)))/2:.3f}' for v in x]
    return f'{len(mu)} {m} {len(x)}\n'+' '.join(map(thousand,mu))+'\n'+' '.join(map(thousand,sigma))+'\n'+' '.join(map(thousand,x))+'\n'+' '.join(phi)+'\n'

def lookup_boundaries():
    # Exact rational midpoints that binary floating arithmetic may move right,
    # plus values genuinely on either side and table endpoints.
    return [normal_case([996],[2000],1,[0,4]),
            normal_case([700],[2000],1,[100,200]),
            normal_case([400],[2000],1,[0,200,400,1000]),
            normal_case([996],[1999],1,[0,4]),
            normal_case([996],[2001],1,[0,4]),
            normal_case([999],[1000],1,[1,4]),
            normal_case([1],[1000],1,[0,999]),
            normal_case([333,333,330],[1200,1600,1],1,[0,4])]
def random_normal(rng,n):
    sigma=[rng.randint(1,10000) for _ in range(n)];root=math.isqrt(sum(v*v for v in sigma));delta=rng.randint(0,min(root,99000))
    minimum=max(1,(delta+n+999)//1000);m=rng.randint(minimum,100);target=m*1000-delta
    cuts=[0]+sorted(rng.sample(range(1,target),n-1))+[target]
    return normal_case([b-a for a,b in zip(cuts,cuts[1:])],sigma,m)
def benefit_case(mu,sigma,m=1,q=1000):return f'{len(mu)} {m} {thousand(q)}\n'+' '.join(map(str,mu))+'\n'+' '.join(map(tenth,sigma))+'\n'
def scheduler_case(slices,work,preferences,T):
    return f'{len(work)} {len(slices)} {T}\n'+' '.join(map(str,slices))+'\n'+''.join(f'{a} {len(p)}'+(' '+' '.join(map(str,p)) if p else '')+'\n' for a,p in zip(work,preferences))
def grouping_case(values,k=2,op=1):return f'{len(values)} {k} {op}\n'+' '.join(map(str,values))+'\n'

def singleton_group_regressions():
    return [grouping_case([1]),grouping_case([10**18])]

def initial_tree_regressions(small_only=False):
    rng=random.Random(SEED+430100)
    cases=['1 40 4 0\n1\n40\n',
            '2 2 3 0\n11\n1 2\n1 2 3\n',
            '1 40 4 6\n0\n40\n1\n1\n1\n1\n1\n1\n']
    if not small_only:
        cases += [tree_case(2000,40,4,0,'random',rng,state_mode='on'),
                  tree_case(100000,40,4,0,'star',rng,state_mode='on')]
    return cases
def tree_case(n,m,k,q,shape,rng,monochrome=False,state_mode='random',weight_multiple=False):
    colors=[1]*n if monochrome else [rng.randint(1,m) for _ in range(n)]
    state=('1'*n if state_mode=='on' else '0'*n if state_mode=='off' else ''.join(rng.choice('01') for _ in range(n)))
    edges=[]
    for v in range(2,n+1):
        u=1 if shape=='star' else v-1 if shape=='chain' else v//2 if shape=='binary' else rng.randint(1,v-1)
        w=rng.randint(1,10**6//k)*k if weight_multiple else rng.randint(1,10**6)
        edges.append((u,v,w))
    toggles=[rng.randint(1,n) for _ in range(q)]
    if q>=4:toggles[:4]=[1,1,n,n]
    return f'{n} {m} {k} {q}\n'+state+'\n'+' '.join(map(str,colors))+'\n'+''.join(f'{u} {v} {w}\n' for u,v,w in edges)+''.join(f'{u}\n' for u in toggles)

def small_cases(position):
    rng=random.Random(SEED+position)
    if position==1:yield from lookup_boundaries()
    if position==4:yield from singleton_group_regressions()
    if position==5:yield from initial_tree_regressions(small_only=True)
    for index in range(40):
        if position==1:yield random_normal(rng,rng.randint(1,8))
        elif position==2:
            n=rng.randint(1,12);yield benefit_case([rng.randint(1,100) for _ in range(n)],[rng.randint(1,30) for _ in range(n)],rng.randint(1,10),rng.randint(500,1000))
        elif position==3:
            n,m=rng.randint(1,8),rng.randint(1,8);yield scheduler_case([rng.randint(1,8) for _ in range(m)],[rng.randint(1,12) for _ in range(n)],[rng.sample(range(1,m+1),rng.randint(0,m)) for _ in range(n)],rng.randint(1,8))
        elif position==4:yield grouping_case(rng.sample(range(1,100),rng.randint(1,10)),rng.randint(2,7),rng.randrange(2))
        else:yield tree_case(rng.randint(1,18),rng.randint(1,8),rng.randint(1,4),rng.randint(1,20),rng.choice(['star','chain','binary','random']),rng)

def dataset(position):
    rng=random.Random(SEED+100+position)
    if position==1:
        cases=[normal_case([1000],[1000],1,[0,1000]),normal_case([1000],[2000],2,[400,600]),normal_case([1],[1000],1,[0,999]),normal_case([999],[1000],1,[0,4,1000]),normal_case([1000],[10000],11,[0,500,1000])]
        # Keep the RNG sequence of the other fifteen existing formal points.
        for _ in range(5):random_normal(rng,1)
        cases += lookup_boundaries()[:5]
        cases += [normal_case([10]*99+[5],[1]*100,1),normal_case([600,800],[600,800],2,[0,600,1000])]
        cases += [random_normal(rng,100) for _ in range(8)]
        return cases
    if position==2:
        cases=[benefit_case([7],[30]),benefit_case([9],[10]),benefit_case([9,9],[6,8]),benefit_case([100]*100,[1]*100,10,500),benefit_case([1]*100,[30]*100,1,1000)]
        cases += [benefit_case([rng.randint(1,100)]*100,[rng.randint(1,30) for _ in range(100)],rng.randint(1,10),rng.randint(500,1000)) for _ in range(11)]
        cases += [benefit_case([5,8,7],[10,6,8]),benefit_case([100,60,60],[10,7,7]),benefit_case(list(range(1,101)),[30]*100,10,500),benefit_case([rng.randint(1,100) for _ in range(100)],[rng.randint(1,30) for _ in range(100)],10,999)]
        return cases
    if position==3:
        cases=[scheduler_case([100],[1],[[]],10**9),scheduler_case([1],[3],[[1]],10**9),scheduler_case([2],[3,2],[[],[1]],10**9),scheduler_case([1]*100,[100]*100,[list(range(1,101))]*100,10**9)]
        for _ in range(4):
            n,m=100,rng.randint(1,100);cases.append(scheduler_case([rng.randint(1,100) for _ in range(m)],[rng.randint(1,100) for _ in range(n)],[rng.sample(range(1,m+1),rng.randint(0,m)) for _ in range(n)],10**9))
        cases += [scheduler_case([1,1],[3,3],[[],[]],1),scheduler_case([1]*100,[1],[[]],1)]
        for _ in range(6):
            n,m=100,rng.randint(1,100);cases.append(scheduler_case([1]*m,[rng.randint(1,100) for _ in range(n)],[rng.sample(range(1,m+1),rng.randint(0,m)) for _ in range(n)],rng.randint(1,20)))
        cases += [scheduler_case([2,1],[7,5,3,4],[[],[1],[2],[1,2]],2),scheduler_case([3,2],[5,7,3],[[2],[1],[]],1),scheduler_case([100,100],[100]*100,[[]]*100,3),scheduler_case([7]*10,[rng.randint(1,100) for _ in range(100)],[[]]*100,7)]
        return cases
    if position==4:
        cases=[grouping_case([4,8,16,11,32]),grouping_case([4,12])]
        cases += [grouping_case([1,2,4],2,0),grouping_case([10**18-1,10**18],10**9,0),grouping_case(list(range(1,2001)),2,0),grouping_case(rng.sample(range(1,100000),2000),3,0)]
        cases += [grouping_case(list(range(1,500001)),2,0),grouping_case(list(range(1,250001))+[10**9*x for x in range(1,250001)],10**9,0),grouping_case([10**18-i for i in range(100000)],2,0),grouping_case(list(range(1,100001)),10**9,0),grouping_case(rng.sample(range(1,10**7),100000),7,0)]
        cases += [grouping_case(list(range(1,2001)),2,1),grouping_case([4,11],2,1),grouping_case([10**18-1,10**18],10**9,1),grouping_case(rng.sample(range(1,100000),2000),5,1)]
        cases += [grouping_case(list(range(1,500001)),2,1),grouping_case(list(range(1,250001))+[10**9*x for x in range(1,250001)],10**9,1),grouping_case([10**18-i for i in range(100000)],2,1),grouping_case([4,8,16,11,32]+list(range(10**18-99994,10**18+1)),2,1),grouping_case(list(range(1,100001)),2,1)]
        return cases+singleton_group_regressions()
    cases=[tree_case(2000,40,4,2000,shape,rng) for shape in ['chain','binary','random']]
    cases += [tree_case(100000,1,1,100000,shape,rng,True,'on') for shape in ['chain','star','random']]
    cases += [tree_case(100000,40,1,100000,'star',rng,state_mode=mode) for mode in ['on','off','random','random']]
    cases += [tree_case(100000,4,1,100000,shape,rng,state_mode=mode) for shape,mode in [('chain','on'),('star','random'),('chain','random'),('star','off')]]
    cases += [tree_case(100000,40,4,100000,shape,rng,state_mode=mode) for shape,mode in [('star','on'),('chain','on'),('star','off'),('chain','random')]]
    cases += [tree_case(100000,40,4,100000,shape,rng,True,'on',True) for shape in ['binary','random']]
    return cases+initial_tree_regressions()
