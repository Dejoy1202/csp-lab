"""Original deterministic fixtures and independent answer models for CSP201412."""
from collections import deque
from functools import lru_cache
from itertools import combinations,product
import bisect
import heapq
import random
import re
SEED=2014121403
ORACLE_DESCRIPTION='Direct prefix enumeration; boundary-bouncing zigzag; separate buy/sell prefix sums cross-checked by enumeration; Prim cross-checked by spanning-tree enumeration; full-supply SPFA min-cost flow cross-checked by cyclic inventory DP'
INF=10**30

def read(position,text):
    if position==3:
        records=[]
        for row in text.splitlines():
            fields=row.split()
            if fields[0]=='cancel':records[int(fields[1])-1][3]=False;records.append(['cancel',0,0,False])
            else:records.append([fields[0],int(fields[1].replace('.','')),int(fields[2]),True])
        return records
    values=list(map(int,text.split()))
    if position==1:return values[0],values[1:]
    if position==2:return values[0],[values[1+i*values[0]:1+(i+1)*values[0]] for i in range(values[0])]
    n,m=values[:2]
    if position==4:return n,[tuple(values[2+3*i:5+3*i]) for i in range(m)]
    off=2+16*n
    return n,[values[2+16*i:18+16*i] for i in range(n)],[tuple(values[off+3*i:off+3*i+3]) for i in range(m)]

def validate(position,text):
    assert text.endswith('\n')
    if position==3:
        rows=text.splitlines();assert 2<=len(rows)<=5000;active=[]
        for i,row in enumerate(rows):
            f=row.split()
            if f[0]=='cancel':
                assert len(f)==2 and 1<=int(f[1])<=i and active[int(f[1])-1];active[int(f[1])-1]=False;active.append(False)
            else:
                assert f[0] in ('buy','sell') and len(f)==3 and re.fullmatch(r'[0-9]+\.[0-9]{2}',f[1])
                assert 1<=int(f[1].replace('.',''))<=1000000 and 1<=int(f[2])<=10**8;active.append(True)
        assert int(auction(read(3,text)).split()[1])>0,'Zero-trade opening price is undefined by original statement';return
    values=list(map(int,text.split()))
    if position==1:
        n,a=read(1,text);assert 1<=n<=1000 and len(a)==n and all(1<=x<=n for x in a)
    elif position==2:
        n,a=read(2,text);assert 1<=n<=500 and len(values)==n*n+1 and all(1<=x<=1000 for row in a for x in row)
    elif position==4:
        n,e=read(4,text);assert 1<=n<=1000 and 1<=len(e)<=100000 and len(values)==2+3*len(e)
        assert all(1<=a<=n and 1<=b<=n and a!=b and 1<=w<=10000 for a,b,w in e)
        assert prim(n,e)<INF
    else:
        n,rows,e=read(5,text);assert 1<=n<=100 and 1<=len(e)<=500 and len(values)==2+16*n+3*len(e)
        assert all(len(r)==16 and all(0<=x<=100 for x in r[:15]) and 1<=r[15]<=100 for r in rows)
        assert sum(sum(r[:7]) for r in rows)==sum(sum(r[7:14]) for r in rows)
        assert all(1<=a<=n and 1<=b<=n and a!=b and 1<=w<=100 for a,b,w in e)
        assert len({tuple(sorted((a,b))) for a,b,w in e})==len(e)

def auction(orders):
    active=[r for r in orders if r[3]];prices=sorted({r[1] for r in active})
    buys=sorted((p,s) for t,p,s,on in active if t=='buy');sells=sorted((p,s) for t,p,s,on in active if t=='sell')
    bp=[p for p,s in buys];sp=[p for p,s in sells];bc=[0];sc=[0]
    for p,s in buys:bc.append(bc[-1]+s)
    for p,s in sells:sc.append(sc[-1]+s)
    volumes=[(min(bc[-1]-bc[bisect.bisect_left(bp,p)],sc[bisect.bisect_right(sp,p)]),p) for p in prices]
    best,p=max(volumes)
    if len(orders)<=60:
        brute=max((min(sum(s for t,v,s,on in active if t=='buy' and v>=p),sum(s for t,v,s,on in active if t=='sell' and v<=p)),p) for p in prices)
        assert (best,p)==brute
    return f'{p//100}.{p%100:02d} {best}\n'

def prim(n,edges):
    graph=[[] for _ in range(n)]
    for a,b,w in edges:graph[a-1].append((w,b-1));graph[b-1].append((w,a-1))
    used=set();heap=[(0,0)];cost=0
    while heap and len(used)<n:
        w,u=heapq.heappop(heap)
        if u in used:continue
        used.add(u);cost+=w
        for item in graph[u]:
            if item[1] not in used:heapq.heappush(heap,item)
    return cost if len(used)==n else INF

def tree_enumeration(n,edges):
    best=INF
    for selected in combinations(edges,n-1):
        parents=list(range(n))
        def root(u):
            while parents[u]!=u:u=parents[u]
            return u
        cost=0
        for a,b,w in selected:
            a,b=root(a-1),root(b-1)
            if a==b:break
            parents[a]=b;cost+=w
        else:best=min(best,cost)
    return best

def mincost(n,rows,edges):
    # Model every production and every consumption, unlike net-balance reference.
    source=7*n;sink=source+1;graph=[[] for _ in range(sink+1)]
    def add(a,b,capacity,cost):
        graph[a].append([b,len(graph[b]),capacity,cost]);graph[b].append([a,len(graph[a])-1,0,-cost])
    required=0
    for city,r in enumerate(rows):
        for day in range(7):
            u=7*city+day;add(source,u,r[day],0);required+=r[day];add(u,sink,r[day+7],0);add(u,7*city+(day+1)%7,r[14],r[15])
    for a,b,w in edges:
        for d in range(7):add(7*(a-1)+d,7*(b-1)+d,10**6,w);add(7*(b-1)+d,7*(a-1)+d,10**6,w)
    flow=cost=0
    while flow<required:
        distance=[INF]*len(graph);distance[source]=0;previous=[None]*len(graph);queue=deque([source]);queued={source}
        while queue:
            u=queue.popleft();queued.remove(u)
            for index,(v,reverse,capacity,w) in enumerate(graph[u]):
                if capacity and distance[v]>distance[u]+w:
                    distance[v]=distance[u]+w;previous[v]=(u,index)
                    if v not in queued:queue.append(v);queued.add(v)
        assert distance[sink]<INF,'No feasible cyclic schedule'
        pushed=required-flow;v=sink
        while v!=source:
            u,index=previous[v];pushed=min(pushed,graph[u][index][2]);v=u
        v=sink
        while v!=source:
            u,index=previous[v];arc=graph[u][index];arc[2]-=pushed;graph[v][arc[1]][2]+=pushed;v=u
        flow+=pushed;cost+=pushed*distance[sink]
    return cost

def inventory_dp(n,rows,edges):
    # Enumerate exact overnight inventories; no time-expanded flow network.
    distance=[[INF]*n for _ in range(n)]
    for i in range(n):distance[i][i]=0
    for a,b,w in edges:distance[a-1][b-1]=distance[b-1][a-1]=min(w,distance[a-1][b-1])
    for k in range(n):
        for i in range(n):
            for j in range(n):distance[i][j]=min(distance[i][j],distance[i][k]+distance[k][j])
    states=list(product(*(range(r[14]+1) for r in rows)))
    @lru_cache(None)
    def shipping(supply,need):
        if not any(supply):return 0
        u=next(i for i,v in enumerate(supply) if v)
        new=list(supply);new[u]-=1;best=INF
        for v,count in enumerate(need):
            if count and distance[u][v]<INF:
                remaining=list(need);remaining[v]-=1;best=min(best,distance[u][v]+shipping(tuple(new),tuple(remaining)))
        return best
    costs=[]
    for d in range(7):
        matrix=[]
        for before in states:
            row=[]
            for after in states:
                balance=[before[i]+rows[i][d]-rows[i][7+d]-after[i] for i in range(n)]
                if sum(balance):row.append(INF);continue
                travel=shipping(tuple(max(v,0) for v in balance),tuple(max(-v,0) for v in balance))
                row.append(travel+sum(after[i]*rows[i][15] for i in range(n)))
            matrix.append(row)
        costs.append(matrix)
    best=INF
    for start in range(len(states)):
        dp=[INF]*len(states);dp[start]=0
        for d in range(7):dp=[min(dp[i]+costs[d][i][j] for i in range(len(states))) for j in range(len(states))]
        best=min(best,dp[start])
    return best

def oracle(position,text):
    item=read(position,text)
    if position==1:
        n,a=item;return ' '.join(str(a[:i+1].count(x)) for i,x in enumerate(a))+'\n'
    if position==2:
        n,a=item;row=col=0;up=True;answer=[]
        for _ in range(n*n):
            answer.append(a[row][col])
            if up:
                if col==n-1:row+=1;up=False
                elif row==0:col+=1;up=False
                else:row-=1;col+=1
            else:
                if row==n-1:col+=1;up=True
                elif col==0:row+=1;up=True
                else:row+=1;col-=1
        return ' '.join(map(str,answer))+'\n'
    if position==3:return auction(item)
    if position==4:
        n,e=item;answer=prim(n,e)
        if n<=6 and len(e)<=12:assert answer==tree_enumeration(n,e)
        return str(answer)+'\n'
    n,rows,e=item;answer=mincost(n,rows,e)
    if n==100 and e==[(i,i+1,100) for i in range(1,100)]:
        assert rows==[([0]*6+[100]+[0]*7+[100,1] if i<50 else [0]*7+[100]+[0]*6+[100,1]) for i in range(100)]
        assert answer==25005000,'Independent cut-flow and one-night lower bound'
    if n==100 and all(r==[0,0,100,0,100,0,100,0,100,0,100,0,100,0,100,1] for r in rows):
        assert answer==40000,'Aggregate weekly inventory lower bound'
    if n<=3 and all(r[14]<=2 and max(r[:14])<=4 for r in rows):assert answer==inventory_dp(n,rows,e),'SPFA/inventory DP mismatch'
    return str(answer)+'\n'

def numbers(a):return str(len(a))+'\n'+' '.join(map(str,a))+'\n'
def matrix(a):return str(len(a))+'\n'+''.join(' '.join(map(str,row))+'\n' for row in a)
def graph(n,e):return f'{n} {len(e)}\n'+''.join(f'{a} {b} {w}\n' for a,b,w in e)
def logistics(rows,e):return f'{len(rows)} {len(e)}\n'+''.join(' '.join(map(str,r))+'\n' for r in rows)+''.join(f'{a} {b} {w}\n' for a,b,w in e)

def auction_case(rng,count):
    # Protected crossed orders guarantee a well-defined positive opening volume.
    lines=['buy 10000.00 1','sell 0.01 1'];active=[]
    for i in range(2,count):
        if active and rng.random()<.25:
            at=rng.randrange(len(active));line=active.pop(at);lines.append(f'cancel {line}')
        else:
            p=rng.randint(1,1000000);lines.append(f'{rng.choice(["buy","sell"])} {p//100}.{p%100:02d} {rng.randint(1,10**8)}');active.append(i+1)
    return '\n'.join(lines)+'\n'

def graph_case(rng,n,m,equal=False):
    pairs={tuple(sorted((i,rng.randrange(1,i)))) for i in range(2,n+1)}
    while len(pairs)<m:
        a,b=sorted(rng.sample(range(1,n+1),2));pairs.add((a,b))
    e=[(a,b,7 if equal else rng.randint(1,10000)) for a,b in sorted(pairs)];rng.shuffle(e)
    return graph(n,e)

def logistics_case(rng,n,m,small=False):
    pairs={tuple(sorted((i,rng.randrange(1,i)))) for i in range(2,n+1)}
    while len(pairs)<m:pairs.add(tuple(sorted(rng.sample(range(1,n+1),2))))
    e=[(a,b,rng.randint(1,5 if small else 100)) for a,b in sorted(pairs)]
    v=[rng.randint(0,2 if small else 100) for _ in range(n)];w=[rng.randint(1,5 if small else 100) for _ in range(n)]
    # An explicit weekly inventory/transport witness guarantees feasibility.
    stock=[[rng.randint(0,min(v[i],1 if small else 20)) for d in range(7)] for i in range(n)]
    delta=[[stock[i][(d-1)%7]-stock[i][d] for d in range(7)] for i in range(n)]
    for d in range(7):
        for a,b,c in rng.sample(e,min(len(e),1 if small else max(1,n//3))):
            f=rng.randint(0,1 if small else 3);delta[a-1][d]-=f;delta[b-1][d]+=f
    rows=[]
    for i in range(n):
        a=[];b=[]
        for d in range(7):
            diff=delta[i][d];base=rng.randint(0,max(0,(2 if small else 100)-abs(diff)));a.append(base+max(0,-diff));b.append(base+max(0,diff))
        rows.append(a+b+[v[i],w[i]])
    return logistics(rows,e)

def small_cases(position):
    rng=random.Random(SEED+position)
    for i in range(40):
        if position==1:
            n=rng.randint(1,50);yield numbers([rng.randint(1,n) for _ in range(n)])
        elif position==2:
            n=rng.randint(1,12);yield matrix([[rng.randint(1,1000) for _ in range(n)] for _ in range(n)])
        elif position==3:yield auction_case(rng,rng.randint(2,60))
        elif position==4:
            n=rng.randint(2,6);yield graph_case(rng,n,rng.randint(n-1,min(10,n*(n-1)//2)))
        else:
            n=3 if i%5==0 else 2;yield logistics_case(rng,n,rng.randint(n-1,n*(n-1)//2),True)

def dataset(position):
    rng=random.Random(SEED+100+position)
    if position==1:
        fixed=[[1],[2,1],[3,3,3],[4,1,4,1],[5,5,5,5,5],list(range(1,1001)),list(range(1000,0,-1)),[1000]*1000,[1]*1000,[1,1000]*500]
        return [numbers(a) for a in fixed]+[numbers([rng.randint(1,n) for _ in range(n)]) for n in [7,19,50,99,100,249,499,998,999,1000]]
    if position==2:
        cases=[matrix([[9]]),matrix([[1,2],[3,4]]),matrix([[11,12,13],[21,22,23],[31,32,33]])]
        for n in [4,5,9,10,17,31,50,99,100,199,200,499,500,500,500,500,500]:
            mode=len(cases)%4
            a=[[rng.randint(1,1000) if mode==0 else (1 if mode==1 else ((i*397+j*31)%1000+1 if mode==2 else (1000 if (i+j)%2 else 1))) for j in range(n)] for i in range(n)]
            cases.append(matrix(a))
        return cases
    if position==3:
        fixed=['buy 10.00 4\nsell 5.00 4\n','buy 0.01 7\nsell 0.01 7\n','buy 4.25 6\nsell 4.25 6\n','buy 10.00 5\nsell 5.00 5\nbuy 20.00 100\ncancel 3\n','buy 2.00 5\nsell 1.00 5\nbuy 3.00 8\ncancel 1\nsell 2.50 2\ncancel 5\n','buy 7.00 100000000\nsell 7.00 100000000\n','buy 10000.00 2\nsell 9999.99 2\n']
        bulk=('buy 5.25 100000000\n'*2500)+('sell 5.25 100000000\n'*2500)
        return fixed+[bulk]+[auction_case(rng,n) for n in [10,37,100,500,999,1000,2000,3000,4997,4998,4999,5000]]
    if position==4:
        cases=[graph(2,[(1,2,10000)]),graph(3,[(1,2,1),(2,3,1),(1,3,10)]),graph(4,[(1,2,10),(1,3,10),(1,4,10),(2,3,1),(3,4,1)]),graph_case(rng,5,10,True)]
        for n in [8,12,19,20,40,60,99,100,250,500,999,1000,1000,1000,1000,1000]:
            m=100000 if n==1000 and len(cases)>=17 else min(n*(n-1)//2,max(n-1,n*3))
            cases.append(graph_case(rng,n,m,len(cases)%5==0))
        return cases
    zero=logistics([[0]*14+[0,1],[0]*14+[0,100]],[(1,2,100)])
    wrap=logistics([[0,0,0,0,0,0,4]+[0]*7+[4,3],[0]*7+[4,0,0,0,0,0,0]+[4,1]],[(1,2,2)])
    capped=logistics([[0,0,0,0,0,0,4]+[0]*7+[3,3],[0]*7+[4,0,0,0,0,0,0]+[1,1]],[(1,2,2)])
    reverse=logistics([[0]*7+[3,0,0,0,0,0,0]+[0,5],[3,0,0,0,0,0,0]+[0]*7+[0,1]],[(1,2,9)])
    disconnected=logistics([[1]*14+[0,1],[0]*14+[1,2],[0]*14+[2,3]],[(2,3,5)])
    cases=[zero,wrap,capped,reverse,disconnected]+[logistics_case(rng,2,1,True),logistics_case(rng,3,3,True)]
    for n in [5,7,10,20,40,70,99,100,100,100,100,100,100]:
        m=min(500,n*(n-1)//2,max(n-1,n*5));cases.append(logistics_case(rng,n,m))
    chain_rows=[([0]*6+[100]+[0]*7+[100,1] if i<50 else [0]*7+[100]+[0]*6+[100,1]) for i in range(100)]
    cases[-2]=logistics(chain_rows,[(i,i+1,100) for i in range(1,100)])
    dense_edges=read(4,graph_case(rng,100,500))[1]
    cases[-1]=logistics([[0,0,100,0,100,0,100,0,100,0,100,0,100,0,100,1] for _ in range(100)],[(a,b,1) for a,b,w in dense_edges])
    return cases
