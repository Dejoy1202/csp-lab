"""Whitelisted, resource-bounded semantic checking. Never execute user checker code."""
import bisect
import re
from decimal import Decimal, InvalidOperation, localcontext
from sandbox import tokens

TYPES={'TOKENS','FLOAT_ABS_1E_3','FLOAT_ABS_1E_4','CSP_GROUP_COUNT','CSP_GROUP_PARTITION'}

def check_output(kind,input_data,expected,output):
    if kind=='TOKENS':return tokens(output)==tokens(expected.encode('utf-8'))
    if kind in ('FLOAT_ABS_1E_3','FLOAT_ABS_1E_4'):
        fields=output.split(None,2)
        if len(fields)!=1 or len(fields[0])>128:return False
        value=fields[0]
        if not re.fullmatch(rb'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]{1,4})?',value):return False
        try:
            with localcontext() as context:
                context.prec=160
                actual=Decimal(value.decode('ascii'));wanted=Decimal(expected.strip())
                if not actual.is_finite() or abs(actual.as_tuple().exponent)>1000:return False
                return abs(actual-wanted)<Decimal('0.001' if kind=='FLOAT_ABS_1E_3' else '0.0001')
        except (InvalidOperation,ValueError):return False
    if kind not in TYPES:raise ValueError('Unsupported builtin checker')
    # ASCII integer tokens only. Limit both token count and individual lengths,
    # including adversarial output of many zeros or huge decimal integers.
    n,k,op,*values=map(int,input_data.split())
    fields=output.split(None,n+4)
    assert len(values)==n and op in (0,1) and k>=2
    if not fields or len(fields)>n+4 or any(len(t)>19 or not t.isdigit() for t in fields):return False
    count=int(fields[0]);optimal=int(expected.split(None,1)[0])
    if count!=optimal or not 1<=count<=3:return False
    cursor=1;groups=[]
    for _ in range(count):
        if cursor>=len(fields):return False
        size=int(fields[cursor]);cursor+=1
        if size>n or cursor+size>len(fields):return False
        groups.append([int(x) for x in fields[cursor:cursor+size]]);cursor+=size
    if cursor!=len(fields):return False
    if kind=='CSP_GROUP_COUNT':return True
    used=set();wanted=set(values)
    for group in groups:
        for value in group:
            if value not in wanted or value in used:return False
            used.add(value)
        ordered=sorted(group)
        if op==0:
            members=set(group)
            if any(value*k in members for value in group):return False
        else:
            for value in ordered:
                at=bisect.bisect_left(ordered,k*value)
                if at<len(ordered) and ordered[at]<(k+1)*value:return False
    return len(used)==n
