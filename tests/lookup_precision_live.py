"""Actual API regression on the published CSP43 T1, using a separate user."""
import http.cookiejar
import json
import os
from pathlib import Path
import urllib.request
import uuid

import e2e

ROOT=Path(__file__).resolve().parents[1]
e2e.SESSION=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
username='qa_lookup_'+uuid.uuid4().hex[:12]
password=os.environ['ADMIN_INITIAL_PASSWORD']
e2e.api('POST','/api/auth/register',dict(username=username,password=password),201)
e2e.api('POST','/api/auth/login',dict(username=username,password=password))
problem=next(p for p in e2e.api('GET','/api/problems?batch=202609&size=100')['items'] if p['code']=='202609-1')
evidence=[]
exam=e2e.api('POST','/api/exams',dict(batch='202609'),201)
try:
    for name,source,expected in [
        ('double-midpoint',ROOT/'problem-packs/202609/mutants/1-double-nearest.cpp','WA'),
        ('integer-reference',ROOT/'problem-packs/202609/reference/1.cpp','AC'),
    ]:
        result=e2e.submit(problem['id'],source.read_text(encoding='utf-8'),exam['id'])
        assert result['status']==expected,result['status']
        assert (result['score']<100 if expected=='WA' else result['score']==100)
        assert len(result['results'])==20
        row=dict(test=name,submissionId=result['id'],status=result['status'],score=result['score'],testPoints=len(result['results']))
        evidence.append(row)
        print(json.dumps(row),flush=True)
finally:
    e2e.api('POST',f'/api/exams/{exam["id"]}/finish')
receipt=ROOT/'docs/validation/lookup-precision-repair.json'
data=json.loads(receipt.read_text(encoding='utf-8'))
data['liveApiRegression']=evidence
receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
