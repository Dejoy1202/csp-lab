"""Independent verification programs. No submitted code is ever run on the host."""
from collections import Counter
from fractions import Fraction
import re

def one(data):
    it = iter(map(int, data.split()))
    n, m = next(it), next(it)
    total, articles = Counter(), Counter()
    for _ in range(n):
        row = [next(it) for _ in range(next(it))]
        total.update(row)
        articles.update(set(row))
    return "".join(f"{articles[i]} {total[i]}\n" for i in range(1, m + 1))

def two(data):
    words = data.split()
    n, m = map(int, words[:2])
    a = {w.lower() for w in words[2:2+n]}
    b = {w.lower() for w in words[2+n:2+n+m]}
    return f"{len(a & b)}\n{len(a | b)}\n"

def three(data):
    it = iter(data.split())
    answer = []
    for _ in range(int(next(it))):
        m = int(next(it))
        formulas = [dict((e, int(v)) for e, v in re.findall(r"([a-z]+)([0-9]+)", next(it))) for _ in range(m)]
        elements = sorted(set().union(*(f.keys() for f in formulas)))
        a = [[Fraction(f.get(e, 0)) for f in formulas] for e in elements]
        rank = 0
        # Gauss-Jordan over exact rationals, independent of C++ integer elimination.
        for col in range(m):
            pivot = next((r for r in range(rank, len(a)) if a[r][col]), None)
            if pivot is None:
                continue
            a[rank], a[pivot] = a[pivot], a[rank]
            p = a[rank][col]
            a[rank] = [v / p for v in a[rank]]
            for r in range(len(a)):
                if r != rank and a[r][col]:
                    factor = a[r][col]
                    a[r] = [x - factor*y for x, y in zip(a[r], a[rank])]
            rank += 1
        answer.append("Y" if rank < m else "N")
    return "\n".join(answer) + "\n"

def four(data):
    it = iter(map(int, data.split()))
    c, m, n = next(it), next(it), next(it)
    water = {next(it): next(it) for _ in range(m)}
    answer = []
    for _ in range(n):
        x = next(it)
        assert x in water
        water[x] += 1
        while True:
            unstable = [p for p, w in water.items() if w >= 5]
            if not unstable:
                break
            p = min(unstable)
            del water[p]
            left = max((v for v in water if v < p), default=None)
            right = min((v for v in water if v > p), default=None)
            for v in (left, right):
                if v is not None:
                    water[v] += 1
        answer.append(str(len(water)))
    return "\n".join(answer) + "\n"

def five(data):
    it = iter(map(int, data.split()))
    n, m = next(it), next(it)
    parent = [0, 0] + [next(it) for _ in range(n - 1)]
    values = [0] + [next(it) for _ in range(n)]
    children = [[] for _ in range(n + 1)]
    for v in range(2, n + 1):
        children[parent[v]].append(v)
    deleted = set()
    answer = []
    for _ in range(m):
        op, x = next(it), next(it)
        assert x not in deleted
        if op == 1:
            old = children[x]
            children[x] = []
            for ch in old:
                values[x] += values[ch]
                deleted.add(ch)
                for v in children[ch]:
                    parent[v] = x
                    children[x].append(v)
                children[ch] = []
            answer.append(f"{len(children[x])} {values[x]}")
        else:
            depth, cur = 0, x
            while cur:
                depth += 1
                cur = parent[cur]
            answer.append(str(depth))
    return "\n".join(answer) + "\n"

ORACLES = [None, one, two, three, four, five]
