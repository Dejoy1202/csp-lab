"""Own deterministic data, range validation and independent answer models."""
from collections import deque
from functools import lru_cache
from itertools import combinations
import random
import re

SEED = 2014031601
ORACLE_DESCRIPTION = "Pair enumeration; timestamp window model; token-state parser; hop-layer resource DP; exact small event scheduling plus bounded assignment feasibility"

def read(position, text):
    if position == 3:
        lines = text.splitlines()
        return lines[0], lines[2:]
    values = list(map(int, text.split()))
    if position == 1:
        return values[1:]
    if position == 2:
        n,m = values[:2]
        return [tuple(values[2+4*i:6+4*i]) for i in range(n)], [tuple(values[2+4*n+2*i:4+4*n+2*i]) for i in range(m)]
    if position == 4:
        n,m,k,r = values[:4]
        return n,k,r,[tuple(values[4+2*i:6+2*i]) for i in range(n+m)]
    return [tuple(values[1+4*i:5+4*i]) for i in range(values[0])]

def graph_of(points,r):
    return [[j for j,q in enumerate(points) if j!=i and (p[0]-q[0])**2+(p[1]-q[1])**2<=r*r] for i,p in enumerate(points)]

def validate(position,text):
    assert text.endswith('\n')
    if position == 3:
        lines=text.splitlines(); fmt=lines[0]
        assert re.fullmatch(r'(?:[a-z]:?)+',fmt) and 1<=len(fmt)<=52
        assert len(set(fmt.replace(':','')))==len(fmt.replace(':',''))
        count=int(lines[1]); assert 1<=count<=20 and len(lines)==count+2
        for line in lines[2:]:
            assert 1<=len(line)<=256 and re.fullmatch(r'[a-z]+(?: [a-z0-9-]+)*',line)
        return
    v=list(map(int,text.split()))
    if position == 1:
        assert 1<=v[0]<=500 and len(v)==v[0]+1 and len(set(v[1:]))==v[0]
        assert all(1<=abs(x)<=1000 for x in v[1:])
    elif position == 2:
        n,m=v[:2]; assert 1<=n<=10 and 1<=m<=10 and len(v)==2+4*n+2*m
        rectangles,clicks=read(position,text)
        for x1,y1,x2,y2 in rectangles:
            assert 0<=x1<x2<=2559 and 0<=y1<y2<=1439
        assert all(0<=x<=2559 and 0<=y<=1439 for x,y in clicks)
    elif position == 4:
        n,m,k,r=v[:4]; assert 2<=n<=100 and 1<=k<=m<=100 and 1<=r<=10**8 and len(v)==4+2*(n+m)
        _,_,_,points=read(position,text)
        assert len(set(points))==n+m and all(abs(x)<=10**8 and abs(y)<=10**8 for x,y in points)
        graph=graph_of(points[:n],r); seen={0}; todo=deque([0])
        while todo:
            for j in graph[todo.popleft()]:
                if j not in seen: seen.add(j); todo.append(j)
        assert 1 in seen, 'Original routers must already connect endpoints'
    elif position == 5:
        assert 1<=v[0]<=40 and len(v)==1+4*v[0] and all(1<=x<=10 for x in v[1:])
    else:
        raise ValueError(position)

def schedule_exact(jobs):
    """Enumerate actual resource reservations and task order, not aggregate loads."""
    @lru_cache(None)
    def solve(mask,cpu_a,cpu_b,gpu):
        if not mask: return max(cpu_a,cpu_b,gpu)
        best=10**6
        for i,(a,b,c,d) in enumerate(jobs):
            if not(mask>>i&1): continue
            rest=mask^(1<<i)
            def offer(x,y,z):
                return solve(rest,min(x,y),max(x,y),z)
            best=min(best,offer(cpu_a+a,cpu_b,gpu),offer(cpu_a,cpu_b+a,gpu))
            start=max(cpu_a,gpu); best=min(best,offer(start+c,cpu_b,start+c))
            start=max(cpu_b,gpu); best=min(best,offer(cpu_a,start+c,start+c))
            start=max(cpu_a,cpu_b); best=min(best,offer(start+b,start+b,gpu))
            start=max(cpu_a,cpu_b,gpu); best=min(best,offer(start+d,start+d,start+d))
        return best
    return solve((1<<len(jobs))-1,0,0,0)

def schedule_feasible(jobs,limit):
    # Keep minimal GPU occupancy for a pair of CPU occupancy budgets.
    frontier={(0,0):0}
    for a,b,c,d in jobs:
        block=min(b,d); nxt={}
        for (x,y),g in frontier.items():
            for xx,yy,gg in ((x+a,y,g),(x,y+a,g),(x+c,y,g+c),(x,y+c,g+c),(x+block,y+block,g+block)):
                if max(xx,yy,gg)>limit: continue
                key=(min(xx,yy),max(xx,yy))
                if gg<nxt.get(key,10**6): nxt[key]=gg
        frontier=nxt
        if not frontier: return False
    return True

def schedule_large(jobs):
    lower=(sum(min(a,2*b,c,2*d) for a,b,c,d in jobs)+1)//2
    upper=sum(min(a,b,c,d) for a,b,c,d in jobs)
    while lower<upper:
        middle=(lower+upper)//2
        if schedule_feasible(jobs,middle): upper=middle
        else: lower=middle+1
    return lower

def oracle(position,text):
    item=read(position,text)
    if position==1:
        return str(sum(a+b==0 for a,b in combinations(item,2)))+'\n'
    if position==2:
        rectangles,clicks=item; timestamps=list(range(len(rectangles))); answer=[]
        for stamp,(x,y) in enumerate(clicks,len(rectangles)):
            hit=[i for i,(x1,y1,x2,y2) in enumerate(rectangles) if x1<=x<=x2 and y1<=y<=y2]
            chosen=max(hit,key=lambda i:timestamps[i]) if hit else None
            answer.append('IGNORED' if chosen is None else str(chosen+1))
            if chosen is not None: timestamps[chosen]=stamp
        return '\n'.join(answer)+'\n'
    if position==3:
        fmt,commands=item; kinds={m.group(1):bool(m.group(2)) for m in re.finditer(r'([a-z])(:?)',fmt)}; answer=[]
        for row,line in enumerate(commands,1):
            words=iter(line.split(' ')[1:]); found={}
            for token in words:
                if len(token)!=2 or token[0]!='-' or token[1] not in kinds: break
                letter=token[1]
                if kinds[letter]:
                    value=next(words,None)
                    if value is None: break
                    found[letter]=value
                else: found[letter]=None
            parts=[]
            for letter in sorted(found):
                parts.append('-'+letter)
                if found[letter] is not None: parts.append(found[letter])
            answer.append('Case '+str(row)+':'+(' '+' '.join(parts) if parts else ''))
        return '\n'.join(answer)+'\n'
    if position==4:
        n,k,r,points=item; graph=graph_of(points,r); need=[10**6]*len(points);need[0]=0
        # Hop-layer DP minimizes additions for each vertex; unlike reference BFS,
        # it does not use additions as a separate queue-state dimension.
        for hops in range(1,len(points)):
            nxt=[10**6]*len(points)
            for i,used in enumerate(need):
                if used>k: continue
                for j in graph[i]: nxt[j]=min(nxt[j],used+(j>=n))
            if nxt[1]<=k: return str(hops-1)+'\n'
            need=nxt
        raise AssertionError('Guaranteed path disappeared')
    if len(item)<=4:
        exact=schedule_exact(item)
        assert exact==schedule_large(item), 'Scheduling reduction disagrees with independent resource reservation model'
        return str(exact)+'\n'
    return str(schedule_large(item))+'\n'

def numbers(values): return str(len(values))+'\n'+' '.join(map(str,values))+'\n'
def windows(rectangles,clicks):
    return f'{len(rectangles)} {len(clicks)}\n'+''.join(' '.join(map(str,row))+'\n' for row in rectangles+clicks)
def network(original,candidates,k,r):
    return f'{len(original)} {len(candidates)} {k} {r}\n'+''.join(f'{x} {y}\n' for x,y in original+candidates)
def jobs_text(jobs): return str(len(jobs))+'\n'+''.join(' '.join(map(str,j))+'\n' for j in jobs)
def commands(fmt,lines): return fmt+'\n'+str(len(lines))+'\n'+'\n'.join(lines)+'\n'

def small_cases(position):
    rng=random.Random(SEED+position)
    for _ in range(40):
        if position==1:
            yield numbers(rng.sample(list(range(-12,0))+list(range(1,13)),rng.randint(1,24)))
        elif position==2:
            rect=[]
            for _ in range(rng.randint(1,10)):
                x,y=rng.randrange(8),rng.randrange(8); rect.append((x,y,x+rng.randint(1,8),y+rng.randint(1,8)))
            yield windows(rect,[(rng.randrange(18),rng.randrange(18)) for _ in range(rng.randint(1,10))])
        elif position==3:
            chars=rng.sample('abcdefghxyz',rng.randint(1,8)); fmt=''.join(c+(':' if rng.randrange(2) else '') for c in chars)
            lines=[]
            for _ in range(rng.randint(1,20)):
                tokens=[rng.choice(['cmd','tool','run'])]
                for _ in range(rng.randint(0,20)):
                    tokens.append(rng.choice(['-'+rng.choice(chars),'word','-q','--x','-','abc9','-7','42']))
                lines.append(' '.join(tokens))
            yield commands(fmt,lines)
        elif position==4:
            n=rng.randint(2,9); pts=[(i*3,0) for i in range(n)]; original=[pts[0],pts[-1]]+pts[1:-1]
            pool=[(x,y) for x in range(3*n) for y in range(1,5)];cand=rng.sample(pool,rng.randint(1,8))
            yield network(original,cand,rng.randint(1,len(cand)),rng.randint(3,8))
        else:
            yield jobs_text([tuple(rng.randint(1,6) for _ in range(4)) for _ in range(rng.randint(1,4))])

def dataset(position):
    rng=random.Random(SEED+100+position)
    if position==1:
        cases=[[1000],[-1000],[-1000,1000],[-9,7,9,-2,2,4],list(range(1,501)),list(range(-500,0)),list(range(-250,0))+list(range(1,251)),[-1000,-1,1,999],[-5,5,10]]
        cases += [rng.sample(list(range(-1000,0))+list(range(1,1001)),500 if i%2==0 else rng.randint(2,500)) for i in range(11)]
        return [numbers(c) for c in cases]
    if position==2:
        cases=[windows([(0,0,1,1)],[(0,0),(1,1),(2,1)]),windows([(0,0,5,5),(1,1,6,6)],[(0,0),(2,2),(6,6),(2,2)]),windows([(0,0,2559,1439)],[(2559,1439),(0,1439),(2559,0)]),windows([(0,0,1,1),(0,0,1,1)],[(0,0)]*10)]
        for i in range(16):
            rect=[]
            for _ in range(10):
                x,y=rng.randrange(2559),rng.randrange(1439); rect.append((x,y,rng.randint(x+1,2559),rng.randint(y+1,1439)))
            clicks=[rng.choice([(w[0],w[1]),(w[2],w[3]),(rng.randrange(2560),rng.randrange(1440))]) for w in rect]
            cases.append(windows(rect,clicks))
        return cases
    if position==3:
        cases=[commands('a',['tool']),commands('ab:c',['tool -c -b -a -a','run -b one -b two -c','cmd -a file -c','app -b']),commands('a:',['program -a -a','program -a one -a','program -a --']),commands('abc',['run -c -b -a -c','run --a -b','run -a -z -b']),commands('ab:',['run -b -a','run -b x -b -a -a']),commands('z:yx:',['run -x abc -z 9 -y'])]
        cases.append(commands('a:',['cmd -a '+'x'*249]))
        cases += list(small_cases(3))[:12]
        cases.append(commands(''.join(c+':' for c in 'abcdefghijklmnopqrstuvwxyz'),['command '+' '.join('-'+c+' '+str(i) for i,c in enumerate('abcdefghijklmnopqrstuvwxyz')) for _ in range(20)]))
        return cases
    if position==4:
        cases=[network([(0,0),(1,0)],[(2,0)],1,1),network([(0,0),(6,0),(0,3),(3,3),(6,3)],[(3,0)],1,3),network([(-10**8,0),(0,0)],[(10**8,0)],1,10**8)]
        # A U-shaped old route; short straight route needs three new routers.
        old=[(0,0),(12,0),(0,3),(0,6),(3,6),(6,6),(9,6),(12,6),(12,3)]
        for k in (1,2,3): cases.append(network(old,[(3,0),(6,0),(9,0)],k,3))
        cases.append(network([(0,0),(3,4)],[(0,4)],1,5))
        cases.append(network([(0,0),(200000,0),(100000,0)],[(300000,0)],1,100000))
        for i in range(12):
            n=100 if i<6 else rng.randint(3,60)
            pts=[(j*5-10**7,i*300) for j in range(n)]
            old=[pts[0],pts[-1]]+pts[1:-1]
            pool=[(j*5-10**7+2,i*300+offset) for j in range(n) for offset in (1,2)]
            candidates=rng.sample(pool,100 if i<6 else rng.randint(1,min(100,len(pool))))
            cases.append(network(old,candidates,rng.randint(1,len(candidates)),5 if i%2 else 12))
        return cases
    # Include non-monotonic durations, odd partition, cross-CPU GPU scheduling,
    # and mixed maximum n. These expose fastest-mode and one-GPU-CPU greedies.
    cases=[[(1,10,10,10)],[(10,1,10,10)],[(10,10,1,10)],[(10,10,10,1)],[(3,9,9,9),(4,9,9,9)],[(10,10,2,10)]*2,[(10,10,2,10),(10,10,3,10),(4,10,10,10),(4,10,10,10)],[(10,10,10,10)]*40,[(1,10,10,10)]*39,[(10,1,10,10)]*40]
    cases += [[tuple(rng.randint(1,10) for _ in range(4)) for _ in range(40 if i<6 else rng.randint(5,40))] for i in range(10)]
    return [jobs_text(c) for c in cases]
