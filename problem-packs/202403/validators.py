"""Validate syntax, original limits, legal operations and subtask properties."""
import re

def validate(position, data, group=None):
    text = data.split()
    if position == 1:
        it = iter(map(int, text)); n, m = next(it), next(it)
        assert 1 <= n <= 100 and 1 <= m <= 100
        for _ in range(n):
            k = next(it); assert 1 <= k <= 100
            for _ in range(k): assert 1 <= next(it) <= m
        assert next(it, None) is None
    elif position == 2:
        n, m = map(int, text[:2]); assert 1 <= n <= 10000 and 1 <= m <= 10000
        assert len(text) == n+m+2
        assert all(re.fullmatch(r"[a-zA-Z]{1,10}", w) for w in text[2:])
        if group == "small": assert n <= 100 and m <= 100 and all(w.islower() for w in text[2:])
    elif position == 3:
        it = iter(text); n = int(next(it)); assert 1 <= n <= 10
        limit = {"s1":2, "s2":3, "s3":40}.get(group, 40)
        for _ in range(n):
            m = int(next(it)); assert 1 <= m <= limit
            elements = set()
            for _ in range(m):
                s = next(it); parts = re.findall(r"([a-z]+)([0-9]+)", s)
                assert "".join(e+v for e,v in parts) == s and parts
                assert len({e for e,v in parts}) == len(parts)
                assert all(1 <= int(v) <= 50 for e,v in parts)
                elements.update(e for e,v in parts)
            assert len(elements) <= limit
        assert next(it, None) is None
    elif position == 4:
        it = iter(map(int, text)); c,m,n = next(it),next(it),next(it)
        limits = {"s1":(30,30),"s2":(3000,3000),"s3":(3000,3000),"s4":(10**9,3000),"s5":(300000,300000),"s6":(10**9,300000),"s7":(10**9,300000)}
        max_c,max_m = limits.get(group,(10**9,300000))
        assert 1 <= c <= max_c and 1 <= m <= min(c,max_m) and 1 <= n <= 4*m
        water={}
        for _ in range(m):
            x,w=next(it),next(it); assert 1 <= x <= c and 1 <= w <= 4 and x not in water; water[x]=w
        ops=[next(it) for _ in range(n)]; assert next(it,None) is None
        if m <= 3000:
            for x in ops:
                assert x in water; water[x]+=1
                while True:
                    unstable=[p for p,w in water.items() if w>=5]
                    if group in ("s1","s2","s6"): assert len(unstable)<=1
                    if not unstable: break
                    p=min(unstable);del water[p]
                    left=max((v for v in water if v<p),default=None)
                    right=min((v for v in water if v>p),default=None)
                    for v in (left,right):
                        if v is not None: water[v]+=1
        else:
            # Linear linked simulation verifies large inputs and the S property.
            import heapq
            positions=sorted(water); index={x:i for i,x in enumerate(positions)}
            levels=[water[x] for x in positions]; alive=[True]*m
            prev=[i-1 for i in range(m)]; following=[i+1 for i in range(m)];following[-1]=-1
            for x in ops:
                assert x in index and alive[index[x]]
                p=index[x];levels[p]+=1;pending=[]
                if levels[p]>=5: heapq.heappush(pending,p)
                while pending:
                    if group in ("s1","s2","s6"): assert len(pending)<=1
                    p=heapq.heappop(pending);alive[p]=False
                    left,right=prev[p],following[p]
                    if left!=-1: following[left]=right
                    if right!=-1: prev[right]=left
                    for q in (left,right):
                        if q!=-1:
                            levels[q]+=1
                            if levels[q]==5: heapq.heappush(pending,q)
    elif position == 5:
        it=iter(map(int,text));n,m=next(it),next(it)
        max_n={"s1":500,"s2":5000,"s3":100000}.get(group,500000)
        assert 1<=n<=max_n and 1<=m<=3*n
        parents=[0,0]+[next(it) for _ in range(n-1)]
        children=[[] for _ in range(n+1)]
        for v in range(2,n+1):
            p=parents[v];assert 1<=p<=n;children[p].append(v)
            if group=="s4": assert p==v-1
            if group=="s5": assert p==1
        stack=[1];seen=set()
        while stack:
            v=stack.pop();assert v not in seen;seen.add(v);stack.extend(children[v])
        assert len(seen)==n
        for _ in range(n): assert 0<=next(it)<=100000
        deleted=set()
        for _ in range(m):
            op,x=next(it),next(it);assert op in (1,2) and 1<=x<=n and x not in deleted
            if group=="s6" and op==1: assert x==1
            if group=="s7": assert op==1
            if group=="s8": assert op==2
            if op==1:
                old=children[x];children[x]=[]
                for ch in old: children[x].extend(children[ch]);children[ch]=[];deleted.add(ch)
        assert next(it,None) is None
    return True
