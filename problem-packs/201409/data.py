"""Independent oracles and deterministic boundary data for CSP 201409."""
from collections import deque,Counter
from functools import lru_cache
from itertools import combinations
import random
import re

SEED=2014091401
MOD=1000000007
ORACLE_DESCRIPTION='Pair enumeration; sweep-line interval union; direct character comparisons; per-customer reverse BFS with checked analytic extremes; exact-cover enumeration and verified linear recurrence'

def read(position,text):
    if position==3:
        words=text.split();return words[0],int(words[1]),words[3:]
    v=list(map(int,text.split()))
    if position==1:return v[1:]
    if position==2:return [tuple(v[1+4*i:5+4*i]) for i in range(v[0])]
    if position==5:return tuple(v)
    n,m,k,d=v[:4];off=4
    stores=[tuple(v[off+2*i:off+2*i+2]) for i in range(m)];off+=2*m
    clients=[tuple(v[off+3*i:off+3*i+3]) for i in range(k)];off+=3*k
    blocks=[tuple(v[off+2*i:off+2*i+2]) for i in range(d)]
    return n,stores,clients,set(blocks)

def validate(position,text):
    assert text.endswith('\n')
    if position==3:
        words=text.split();assert len(words)>=4 and words[1] in ('0','1')
        n=int(words[2]);assert 1<=n<=100 and len(words)==n+3
        assert all(1<=len(s)<=100 and re.fullmatch('[a-zA-Z]+',s) for s in [words[0]]+words[3:]);return
    v=list(map(int,text.split()))
    if position==1:
        n=v[0];assert 1<=n<=1000 and len(v)==n+1 and len(set(v[1:]))==n and all(0<=x<=10000 for x in v[1:])
    elif position==2:
        n=v[0];assert 1<=n<=100 and len(v)==1+4*n
        assert all(0<=a<=c<=100 and 0<=b<=d<=100 for a,b,c,d in read(2,text))
    elif position==5:
        assert len(v)==2 and 1<=v[0]<=10**15 and 1<=v[1]<=7
    else:
        n,m,k,d=v[:4];assert 1<=n<=1000 and all(1<=x<=n*n for x in (m,k,d)) and len(v)==4+2*m+3*k+2*d
        n,stores,clients,blocks=read(4,text)
        assert len(blocks)==d
        assert all(1<=x<=n and 1<=y<=n for x,y in stores+list(blocks))
        assert all(1<=x<=n and 1<=y<=n and 1<=c<=1000 for x,y,c in clients)
        assert all(p not in blocks for p in stores) and all((x,y) not in blocks for x,y,c in clients)
        if n<=100:
            seen=set(stores);todo=deque(stores)
            while todo:
                x,y=todo.popleft()
                for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 1<=xx<=n and 1<=yy<=n and (xx,yy) not in blocks and (xx,yy) not in seen:seen.add((xx,yy));todo.append((xx,yy))
            assert all((x,y) in seen for x,y,c in clients),'Customer unreachable'
        else:
            # All large fixtures have an independently proved path shape.
            analytic_delivery(n,stores,clients,blocks)

def analytic_delivery(n,stores,clients,blocks):
    stores_set=set(stores)
    if all((x,y) in stores_set for x,y,c in clients):
        return 0
    if stores==[(1,1)] and blocks=={(2,2)}:
        assert all((x,y)!=(2,2) for x,y,c in clients)
        return sum((x+y-2)*c for x,y,c in clients)
    if stores==[(1,1)] and blocks=={(x,2) for x in range(1,n)}:
        assert all(y>=3 for x,y,c in clients)
        return sum((2*n-x+y-2)*c for x,y,c in clients)
    raise AssertionError('No proved analytic oracle for large fixture')

def delivery_oracle(n,stores,clients,blocks):
    if n>100:return analytic_delivery(n,stores,clients,blocks)
    store_set=set(stores);cache={};answer=0
    for x,y,c in clients:
        if (x,y) not in cache:
            todo=deque([(x,y,0)]);seen={(x,y)}
            while todo:
                xx,yy,distance=todo.popleft()
                if (xx,yy) in store_set:cache[x,y]=distance;break
                for a,b in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                    if 1<=a<=n and 1<=b<=n and (a,b) not in blocks and (a,b) not in seen:seen.add((a,b));todo.append((a,b,distance+1))
            assert (x,y) in cache
        answer+=cache[x,y]*c
    return answer

@lru_cache(None)
def exact_cover(n,m):
    total=n*m
    if total%3:return 0
    full=(1<<total)-1;covers=[[] for _ in range(total)]
    for r in range(n-1):
        for c in range(m-1):
            cells=[r*m+c,r*m+c+1,(r+1)*m+c,(r+1)*m+c+1]
            for missing in range(4):
                mask=sum(1<<p for j,p in enumerate(cells) if j!=missing)
                for j,p in enumerate(cells):
                    if j!=missing:covers[p].append(mask)
    @lru_cache(None)
    def count(used):
        if used==full:return 1
        first=((~used&full)&-(~used&full)).bit_length()-1
        return sum(count(used|piece) for piece in covers[first] if not(used&piece))%MOD
    return count(0)

@lru_cache(None)
def transitions(width):
    full=(1<<width)-1;covers=[[] for _ in range(width)]
    for left in range(width-1):
        cells=[left,left+1,width+left,width+left+1]
        for missing in range(4):
            mask=sum(1<<p for j,p in enumerate(cells) if j!=missing)
            for p in cells[:2]:
                if mask>>p&1:covers[p].append(mask)
    result=[]
    for entry in range(1<<width):
        out=Counter()
        def place(used):
            free=~used&full
            if not free:out[used>>width]+=1;return
            first=(free&-free).bit_length()-1
            for piece in covers[first]:
                if not(used&piece):place(used|piece)
        place(entry);result.append(tuple(out.items()))
    return tuple(result)

def berlekamp_massey(sequence):
    current,previous=[1],[1];length,shift,last=0,1,1
    for index in range(len(sequence)):
        discrepancy=(sequence[index]+sum(current[j]*sequence[index-j] for j in range(1,length+1)))%MOD
        if not discrepancy:shift+=1;continue
        saved=current[:];factor=discrepancy*pow(last,MOD-2,MOD)%MOD
        current += [0]*max(0,len(previous)+shift-len(current))
        for j,coefficient in enumerate(previous):current[j+shift]=(current[j+shift]-factor*coefficient)%MOD
        if 2*length<=index:
            length=index+1-length;previous=saved;last=discrepancy;shift=1
        else:shift+=1
    return [(-x)%MOD for x in current[1:length+1]]

@lru_cache(None)
def tiling_recurrence(width):
    transfer=transitions(width);state=[0]*len(transfer);state[0]=1;sequence=[]
    for _ in range(4*len(transfer)+32):
        sequence.append(state[0]);nxt=[0]*len(state)
        for i,value in enumerate(state):
            if value:
                for j,ways in transfer[i]:nxt[j]=(nxt[j]+value*ways)%MOD
        state=nxt
    training=2*len(transfer)+16
    recurrence=berlekamp_massey(sequence[:training])
    degree=len(recurrence)
    assert degree<=len(transfer)
    # Hold-out terms were not used to derive the recurrence.
    for i in range(training,len(sequence)):
        assert sequence[i]==sum(recurrence[j]*sequence[i-j-1] for j in range(degree))%MOD
    for n in range(1,7):
        if n*width<=36:assert sequence[n]==exact_cover(n,width)
    return tuple(sequence),tuple(recurrence)

def recurrence_term(sequence,recurrence,index):
    if index<len(sequence):return sequence[index]
    length=len(recurrence)
    if not length:return 0
    def multiply(a,b):
        result=[0]*(2*length-1)
        for i,x in enumerate(a):
            if x:
                for j,y in enumerate(b):result[i+j]=(result[i+j]+x*y)%MOD
        for i in range(2*length-2,length-1,-1):
            for j,c in enumerate(recurrence,1):result[i-j]=(result[i-j]+result[i]*c)%MOD
        return result[:length]
    value=[1]+[0]*(length-1);power=([0,1]+[0]*(length-2)) if length>1 else [recurrence[0]]
    while index:
        if index&1:value=multiply(value,power)
        index>>=1
        if index:power=multiply(power,power)
    return sum(x*sequence[i] for i,x in enumerate(value))%MOD

def oracle(position,text):
    item=read(position,text)
    if position==1:return str(sum(abs(a-b)==1 for a,b in combinations(item,2)))+'\n'
    if position==2:
        # Sweep strips and merge y intervals, independently of unit-grid painting.
        xpoints=sorted(set([x for rect in item for x in (rect[0],rect[2])]))
        area=0
        for left,right in zip(xpoints,xpoints[1:]):
            intervals=sorted((b,d) for a,b,c,d in item if a<=left and right<=c and b<d)
            high=-1;length=0
            for bottom,top in intervals:
                start=max(bottom,high)
                if top>start:length+=top-start
                high=max(high,top)
            area+=(right-left)*length
        return str(area)+'\n'
    if position==3:
        pattern,sensitive,lines=item;result=[]
        equal=lambda a,b:a==b if sensitive else a.lower()==b.lower()
        for line in lines:
            if any(all(equal(line[start+j],letter) for j,letter in enumerate(pattern)) for start in range(len(line)-len(pattern)+1)):result.append(line)
        return ''.join(line+'\n' for line in result)
    if position==4:return str(delivery_oracle(*item))+'\n'
    n,m=item
    if n*m%3:return '0\n'
    if n*m<=36:return str(exact_cover(n,m))+'\n'
    sequence,recurrence=tiling_recurrence(m)
    return str(recurrence_term(sequence,recurrence,n))+'\n'

def numbers(a):return str(len(a))+'\n'+' '.join(map(str,a))+'\n'
def rectangles(a):return str(len(a))+'\n'+''.join(' '.join(map(str,row))+'\n' for row in a)
def strings(pattern,option,lines):return pattern+'\n'+str(option)+'\n'+str(len(lines))+'\n'+'\n'.join(lines)+'\n'
def delivery(n,stores,clients,blocks):
    return f'{n} {len(stores)} {len(clients)} {len(blocks)}\n'+''.join(f'{x} {y}\n' for x,y in stores)+''.join(f'{x} {y} {c}\n' for x,y,c in clients)+''.join(f'{x} {y}\n' for x,y in blocks)

def random_delivery(rng,n):
    # Keep all border cells passable; stores at corners, customers on border.
    interior=[(x,y) for x in range(2,n) for y in range(2,n)]
    blocks=rng.sample(interior,rng.randint(1,max(1,len(interior)))) if interior else [(2,2)]
    border=[(x,y) for x in range(1,n+1) for y in range(1,n+1) if (x in (1,n) or y in (1,n)) and (x,y) not in blocks]
    stores=rng.sample(border,rng.randint(1,min(5,len(border))))
    clients=[(*rng.choice(border),rng.randint(1,1000)) for _ in range(rng.randint(1,min(n*n,30)))]
    return delivery(n,stores,clients,blocks)

def small_cases(position):
    rng=random.Random(SEED+position)
    for _ in range(40):
        if position==1:yield numbers(rng.sample(range(40),rng.randint(1,40)))
        elif position==2:
            rect=[]
            for _ in range(rng.randint(1,12)):
                a,c=sorted([rng.randrange(12),rng.randrange(12)]);b,d=sorted([rng.randrange(12),rng.randrange(12)]);rect.append((a,b,c,d))
            yield rectangles(rect)
        elif position==3:
            pattern=''.join(rng.choice('abcABC') for _ in range(rng.randint(1,8)))
            lines=[''.join(rng.choice('abcABC') for _ in range(rng.randint(1,30))) for _ in range(rng.randint(1,20))]
            lines[rng.randrange(len(lines))]=pattern.swapcase()
            yield strings(pattern,rng.randrange(2),lines)
        elif position==4:yield random_delivery(rng,rng.randint(2,8))
        else:yield f'{rng.randint(1,6)} {rng.randint(1,6)}\n'

def dataset(position):
    rng=random.Random(SEED+100+position)
    if position==1:
        fixed=[[0],[10000],[0,1],[9999,10000],list(range(1000)),list(range(999, -1,-1)),list(range(0,2000,2))]
        return [numbers(a) for a in fixed]+[numbers(rng.sample(range(10001),1000 if i<7 else rng.randint(1,1000))) for i in range(13)]
    if position==2:
        fixed=[[(0,0,100,100)],[(0,0,0,0)],[(0,0,100,0)],[(0,0,50,50)]*100,[(0,0,2,2),(1,1,3,3)],[(0,0,1,1),(1,0,2,1)]]
        cases=[rectangles(a) for a in fixed]
        for _ in range(14):
            rect=[]
            for _ in range(100):
                a,c=sorted([rng.randrange(101),rng.randrange(101)]);b,d=sorted([rng.randrange(101),rng.randrange(101)]);rect.append((a,b,c,d))
            cases.append(rectangles(rect))
        return cases
    if position==3:
        cases=[strings('A',0,['a','A','aa','b']),strings('A',1,['a','A','aa','b']),strings('abc',1,['abc','abcd','xabc','ab']),strings('a'*100,0,['A'*100,'a'*99,'b'*100]),strings('ab',0,['ab','AB','ab','Ab']),strings('xyz',1,['aaaa','bbbb'])]
        return cases+list(small_cases(3))[:13]+[strings('a',0,['A'*100]*100)]
    if position==4:
        cases=[random_delivery(rng,2),delivery(3,[(1,1)],[(3,3,2),(1,3,1)],[(2,2)]),delivery(3,[(1,1)],[(3,3,5),(3,3,7)],[(2,2)]),delivery(4,[(1,1),(4,4)],[(1,4,3),(4,1,5)],[(2,2)]),random_delivery(rng,20),random_delivery(rng,20)]
        cases += [random_delivery(rng,100) for _ in range(6)]
        cases += [delivery(250,[(1,1)],[(rng.randint(1,250),250,1000) for _ in range(1000)],[(2,2)]),delivery(1000,[(1,1)],[(1000,1000,1000)]*(10**6),[(2,2)]),delivery(1000,[(1,1)],[(1,1000,1000),(1000,1000,1000)],[(x,2) for x in range(1,1000)]),delivery(1000,[(1,1)],[(1,1,1000)],[(x,y) for x in range(1,1001) for y in range(1,1001) if (x,y)!=(1,1)]),delivery(1000,[(x,y) for x in range(1,1001) for y in range(1,1001) if (x,y)!=(1000,1000)],[(1,1,1000),(999,999,1000)],[(1000,1000)]),delivery(1000,[(1,1)],[(1,1000,1)]*(10**5),[(2,2)]),delivery(1000,[(1,1)],[(1,1000,1000)]*(10**5),[(x,2) for x in range(1,1000)]),delivery(600,[(1,1)],[(1,1,1)],[(x,y) for x in range(1,601) for y in range(1,601) if (x,y)!=(1,1)])]
        return cases
    # Preserve source scale proportions, with two own cases per original point.
    shapes=[(3,2),(30,2),(1,2),(29,2),(2,3),(3,3),(6,6),(5,6),(100,6),(99,5),(1000,6),(999,6),(998,5),(1000,1),(10**15,7),(10**15,6),(10**15-4,7),(10**15-1,6),(10**15-10,5),(999999999999996,7)]
    return [f'{n} {m}\n' for n,m in shapes]
