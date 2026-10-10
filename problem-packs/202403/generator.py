"""Deterministic generators: hand-built traps, random small cases, full boundaries."""
import heapq
import random
import string

SEED = 20240333

def rank_pivot_regressions():
    # Dense random matrices rarely force a zero pivot with TWO nonzero rows
    # below it. Without the row swap, fraction-free elimination loses rank.
    compounds=['a1b1','a1b1c1d1','b1','d1']
    orders=[compounds,compounds[::-1],compounds[1:]+compounds[:1],
            [compounds[i] for i in (0,2,1,3)],
            [compounds[i] for i in (0,1,3,2)],
            [s.replace('1','2') for s in compounds],
            ['a1b1','a1b1c1d1','b1','a2b2c1d1']]
    return ['4 '+' '.join(row) for row in orders]

def make_one(rng, n=10, m=10, repeat=False):
    rows = []
    for _ in range(n):
        k = rng.randint(1,100)
        words = [rng.randint(1,m) for _ in range(k)]
        if repeat: words=[m]*k
        rows.append(str(k)+" "+" ".join(map(str,words)))
    return f"{n} {m}\n"+"\n".join(rows)+"\n"

def make_two(rng, size=100, mixed=False):
    dictionary = ["".join(rng.choices(string.ascii_lowercase,k=rng.randint(1,10))) for _ in range(2*size)]
    a=rng.choices(dictionary,k=size);b=rng.choices(dictionary,k=size)
    if mixed:
        a=["".join(c.upper() if rng.randrange(2) else c for c in s) for s in a]
        b=[s.upper() for s in b]
    return f"{size} {size}\n"+" ".join(a)+"\n"+" ".join(b)+"\n"

def element(i):
    return "e" + chr(97+i//26) + chr(97+i%26)

def make_three(rng, dim):
    equations=[]
    for kind in range(10):
        m=rng.randint(1,dim); e=rng.randint(1,dim)
        a=[[rng.randint(0,50) for _ in range(m)] for _ in range(e)]
        for c in range(m):
            if all(a[r][c]==0 for r in range(e)): a[0][c]=1
        if kind%3==0 and m>1:
            for r in range(e): a[r][-1]=a[r][0]
        if kind%3==1 and e>=m:
            a=[[int(r==c)*rng.randint(1,50) for c in range(m)] for r in range(e)]
        formulas=["".join(element(r)+str(a[r][c]) for r in range(e) if a[r][c]) for c in range(m)]
        equations.append(str(m)+" "+" ".join(formulas))
    return "10\n"+"\n".join(equations)+"\n"

def make_four(rng, m, c, special=False, boundary=False):
    positions=sorted(rng.sample(range(1,c+1),m)) if m<c else list(range(1,m+1))
    # For the S property, a single edge-triggered wave crosses uniform 4-drops.
    levels=[4]*m if special else [rng.randint(1,4) for _ in range(m)]
    original=levels[:];prev=list(range(-1,m-1));following=list(range(1,m))+[-1]
    alive=[True]*m; live_indices=list(range(m));ops=[]
    if special:
        ops=[positions[0]]
    elif boundary:
        # Maximum operation count 4m: first raise every cell from 1 to 4,
        # then initiate a cascade. This gives 3m+1 valid operations.
        original=[1]*m
        ops=[p for p in positions for _ in range(3)]+[positions[0]]
    else:
        for _ in range(min(4*m,max(1,m//2))):
            if not live_indices:break
            p=rng.choice(live_indices);ops.append(positions[p]);levels[p]+=1;pending=[]
            if levels[p]>=5:heapq.heappush(pending,p)
            while pending:
                v=heapq.heappop(pending);alive[v]=False
                a,b=prev[v],following[v]
                if a>=0:following[a]=b
                if b>=0:prev[b]=a
                for q in (a,b):
                    if q>=0:
                        levels[q]+=1
                        if levels[q]==5:heapq.heappush(pending,q)
            if m<=3000:live_indices=[i for i in live_indices if alive[i]]
            elif not alive[p]:
                # Large random cases use valid non-exploding operations in a separate builder.
                live_indices=[i for i in live_indices if alive[i]]
    rows=[f"{p} {w}" for p,w in zip(positions,original)];rng.shuffle(rows)
    return f"{c} {m} {len(ops)}\n"+"\n".join(rows)+"\n"+"\n".join(map(str,ops))+"\n"

def make_five(rng,n,shape="random",group=None):
    parent=[0,0]
    for v in range(2,n+1):
        parent.append(v-1 if shape=="chain" else 1 if shape=="star" else rng.randrange(1,v))
    values=[100000 if n>=100000 else rng.randint(0,100000) for _ in range(n)]
    if group=="s4":
        # Deep iterative DFS, sequential one-level merging and 64-bit accumulation.
        ops=[(2,n)]+[(1,1) for _ in range(n-1)]+[(2,1)]
    elif group=="s5":
        ops=[(2,rng.randint(1,n)) for _ in range(n)]+[(1,1)]+[(2,1)]*(2*n-1)
    elif group=="s8":
        ops=[(2,rng.randint(1,n)) for _ in range(3*n)]
    elif group=="s7":
        # Children have higher IDs, so postorder-like merges always target live folders.
        ops=[(1,v) for v in range(n,0,-1)]
    elif group=="s6":
        ops=[(1,1)]*min(30,n)+[(2,1)]*min(100,2*n)
    else:
        # Permuted non-root IDs test parents that are greater than child IDs.
        permutation=list(range(2,n+1));rng.shuffle(permutation)
        mapping=[0,1]+permutation
        renamed=[0]*(n+1)
        for v in range(2,n+1):renamed[mapping[v]]=mapping[parent[v]]
        parent=renamed;children=[[] for _ in range(n+1)]
        for v in range(2,n+1):children[parent[v]].append(v)
        live=set(range(1,n+1));ops=[]
        for _ in range(min(3*n,3000)):
            x=rng.randint(1,n)
            while x not in live:x=rng.randint(1,n)
            op=1 if rng.randrange(3)==0 else 2;ops.append((op,x))
            if op==1:
                old=children[x];children[x]=[]
                for ch in old:children[x].extend(children[ch]);children[ch]=[];live.remove(ch)
    return f"{n} {len(ops)}\n"+" ".join(map(str,parent[2:]))+"\n"+" ".join(map(str,values))+"\n"+"".join(f"{op} {x}\n" for op,x in ops)

def small_cases(position,count=30):
    if position==3:yield '7\n'+'\n'.join(rank_pivot_regressions())+'\n'
    rng=random.Random(SEED+position)
    for i in range(count):
        if position==1:yield make_one(rng,rng.randint(1,12),rng.randint(1,12),i%7==0)
        elif position==2:yield make_two(rng,rng.randint(1,20),True)
        elif position==3:yield make_three(rng,rng.randint(1,5))
        elif position==4:yield make_four(rng,rng.randint(1,20),30,i%3==0)
        else:yield make_five(rng,rng.randint(1,30))

def dataset(position):
    rng=random.Random(SEED+100*position)
    if position==1:
        cases=["1 1\n1 1\n",make_one(rng,100,100,True)]
        cases += [make_one(rng,100,100) for _ in range(8)]
        return [(s,None,10) for s in cases],[]
    if position==2:
        cases=[make_two(rng,100) for _ in range(8)]+[make_two(rng,10000,True),"3 3\nAbC ABC abc\naBc xYz XYZ\n"]
        return [(s,None,10) for s in cases],[]
    if position==3:
        groups=[("s1",20,2),("s2",40,3),("s3",40,40)]
        cases=[(make_three(rng,dim),key,0) for key,_,dim in groups for _ in range(2)]
        cases.append(("3\n4 c1o1 c1o2 o2 he1\n3 aa1b1 aa2b2 aa3b3\n2 aa50z1 aa49z1\n","s3",0))
        cases.append(('7\n'+'\n'.join(rank_pivot_regressions())+'\n',"s3",0))
        return cases,[{"key":key,"label":f"物质及元素至多 {dim}","score":score} for key,score,dim in groups]
    if position==4:
        specs=[("s1",15,30,30,True),("s2",15,3000,3000,True),("s3",10,3000,3000,False),("s4",15,3000,10**9,False),
               ("s5",15,300000,300000,False),("s6",15,300000,10**9,True),("s7",15,300000,10**9,False)]
        cases=[];groups=[]
        for key,score,m,c,special in specs:
            cases.append((make_four(rng,m,c,special,boundary=m>3000 and not special),key,0))
            cases.append((make_four(rng,min(m,20),min(c,100),special),key,0))
            groups.append({"key":key,"label":f"c≤{c},m≤{m}"+("，性质S" if special else ""),"score":score})
        # Distinguish leftmost-first from rightmost-first cascades; also test n=4m.
        trap="9 5 2\n1 2\n3 4\n5 4\n7 4\n9 1\n5\n1\n"
        for key in ("s3","s4","s5","s7"):cases.append((trap,key,0))
        cases.append(("1 1 4\n1 1\n1\n1\n1\n1\n","s1",0))
        return cases,groups
    specs=[("s1",10,500,None),("s2",15,5000,None),("s3",15,100000,None),("s4",5,500000,"chain"),
           ("s5",5,500000,"star"),("s6",10,500000,None),("s7",15,500000,None),("s8",10,500000,None),("s9",15,500000,None)]
    cases=[];groups=[]
    for key,score,n,shape in specs:
        cases.append((make_five(rng,n,shape or "random",key),key,0))
        cases.append((make_five(rng,min(n,30),shape or "random",key),key,0))
        groups.append({"key":key,"label":f"n≤{n}，"+{"s4":"A","s5":"B","s6":"C","s7":"D","s8":"E"}.get(key,"一般树"),"score":score})
    return cases,groups
