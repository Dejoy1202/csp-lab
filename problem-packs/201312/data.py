"""Original deterministic data, independent oracles and strict validators.
201312 uses the original one-query T4 and original T3 bounds, not OJ extensions.
"""
from collections import Counter, deque
from itertools import product
from math import comb
import random
import re
SEED=20131209

def encode(values): return str(len(values))+"\n"+" ".join(map(str,values))+"\n"
def grid(rows): return str(len(rows))+" "+str(len(rows[0]))+"\n"+"\n".join(rows)+"\n"
def isbn(digits,last): return digits[0]+"-"+digits[1:4]+"-"+digits[4:]+"-"+last+"\n"
def oracle(position,data):
    if position==1:
        values=list(map(int,data.split()))[1:]; count=Counter(values)
        return str(min(count,key=lambda x:(-count[x],x)))+"\n"
    if position==2:
        text=data.strip(); digits=[int(c) for c in text[:-1] if c.isdigit()]
        r=sum((i+1)*d for i,d in enumerate(digits))%11; last="X" if r==10 else str(r)
        return ("Right" if text[-1]==last else text[:-1]+last)+"\n"
    if position==3:
        heights=list(map(int,data.split()))[1:]; answer=0
        # Quadratic enumeration is intentionally independent of the stack reference.
        for l in range(len(heights)):
            low=10001
            for r in range(l,len(heights)):
                low=min(low,heights[r]);answer=max(answer,low*(r-l+1))
        return str(answer)+"\n"
    if position==4:
        n=int(data); answer=sum(comb(n-1,k)*(k-1)*(n-k-1) for k in range(2,n-1))%1000000007
        if n<=8:
            brute=0
            for digits in product(range(4),repeat=n):
                if digits[0]==0 or set(digits)!={0,1,2,3}:continue
                if max(i for i,x in enumerate(digits) if x==0)<min(i for i,x in enumerate(digits) if x==1) and max(i for i,x in enumerate(digits) if x==2)<min(i for i,x in enumerate(digits) if x==3):brute+=1
            assert answer==brute
        return str(answer)+"\n"
    lines=data.splitlines();R,C=map(int,lines[0].split());a=lines[1:];edges={};start=target=None
    directions={"+":((-1,0),(1,0),(0,-1),(0,1)),"S":((-1,0),(1,0),(0,-1),(0,1)),"T":((-1,0),(1,0),(0,-1),(0,1)),"-":((0,-1),(0,1)),"|":((-1,0),(1,0)),".":((1,0),),"#":()}
    for i in range(R):
        for j in range(C):
            if a[i][j]=="S":start=(i,j)
            if a[i][j]=="T":target=(i,j)
            edges[i,j]=[(i+x,j+y) for x,y in directions[a[i][j]] if 0<=i+x<R and 0<=j+y<C and a[i+x][j+y]!="#"]
    def reachable(u):
        seen={u};todo=[u]
        while todo:
            for v in edges[todo.pop()]:
                if v not in seen:seen.add(v);todo.append(v)
        return seen
    reached=reachable(start)
    if target not in reached:return "I'm stuck!\n"
    # Fixed-point reachability, no reverse graph/BFS shared with reference.
    good={target}
    while True:
        added={u for u in reached-good if any(v in good for v in edges[u])}
        if not added:break
        good|=added
    return str(len(reached-good))+"\n"

def validate(position,data):
    if position in (1,3):
        v=list(map(int,data.split()));assert 1<=v[0]<=1000 and len(v)==v[0]+1 and all(1<=x<=10000 for x in v[1:])
    elif position==2:assert re.fullmatch(r"[0-9]-[0-9]{3}-[0-9]{5}-[0-9X]\n?",data)
    elif position==4:assert len(data.split())==1 and 4<=int(data)<=1000
    else:
        lines=data.splitlines();R,C=map(int,lines[0].split());assert 1<=R<=50 and 1<=C<=50 and R*C>=2 and len(lines)==R+1
        chars="".join(lines[1:]);assert all(len(row)==C for row in lines[1:]) and set(chars)<=set("#+-|.ST") and chars.count("S")==1 and chars.count("T")==1

def random_grid(rng,R,C):
    a=[rng.choice("+++-|.#") for _ in range(R*C)];s,t=rng.sample(range(R*C),2);a[s]="S";a[t]="T"
    return grid(["".join(a[i*C:(i+1)*C]) for i in range(R)])
def small_cases(position):
    rng=random.Random(SEED+position)
    for _ in range(20):
        if position in (1,3):yield encode([rng.randint(1,30) for _ in range(rng.randint(1,30))])
        elif position==2:yield isbn("".join(str(rng.randrange(10)) for _ in range(9)),rng.choice("0123456789X"))
        elif position==4:yield str(rng.randint(4,40))+"\n"
        else:yield random_grid(rng,rng.randint(2,6),rng.randint(2,6))
def dataset(position):
    rng=random.Random(SEED+100+position)
    if position==1:
        return [encode(v) for v in [[1],[10000],[5,1,5,1],list(range(1000,0,-1)),[10000]*1000,[i%9+1 for i in range(1000)],*[ [rng.randint(1,10000) for _ in range(1000)] for _ in range(4)]]]
    if position==2:
        return [isbn(d,last) for d,last in [("000000000","0"),("000000000","X"),("123456789","X"),("123456789","0"),("999999999","9"),("100000000","1"),*[ ("".join(str(rng.randrange(10)) for _ in range(9)),rng.choice("0123456789X")) for _ in range(4)]]]
    if position==3:
        return [encode(v) for v in [[1],[10000],[2,4,3,5],[10000]*1000,list(range(1,1001)),list(range(1000,0,-1)),[1,10000]*500,[10000]*499+[1]+[10000]*500,*[ [rng.randint(1,10000) for _ in range(1000)] for _ in range(2)]]]
    if position==4:return [str(n)+"\n" for n in [4,5,6,7,8,25,100,499,999,1000]]
    return [grid(["ST"]),grid(["S#T"]),grid(["S.T"]),grid(["S+T",".#."]),grid(["S","|","T"]),grid(["S"+"+"*48+"T"]),grid(["S"+"+"*49]+["+"*50]*48+["+"*49+"T"]),random_grid(rng,50,50),random_grid(rng,50,1),random_grid(rng,1,50)]
