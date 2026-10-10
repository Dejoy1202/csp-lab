"""Real mock-exam submissions of the three escaped programs and references."""
import http.cookiejar
import gzip
import json
import os
from pathlib import Path
import pymysql
import urllib.request
import uuid
import e2e

ROOT=Path(__file__).resolve().parents[1]
receipt=ROOT/'docs/validation/leakage-repair.json'
data=json.loads(receipt.read_text(encoding='utf-8'))
database_checks=[]
with pymysql.connect(host=os.environ['DB_HOST'],port=int(os.environ.get('DB_PORT','3306')),user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ['DB_NAME'],charset='utf8mb4') as db:
    with db.cursor() as cursor:
        for row in data['published']:
            problem=json.loads(gzip.decompress((ROOT/f'problem-packs/generated/{row["problem"]}.json.gz').read_bytes()))['problems'][0]
            cursor.execute('SELECT code,version,validation_report FROM problems WHERE id=%s',(row['id'],))
            code,version,report=cursor.fetchone()
            assert (code,version)==(row['problem'],row['version'])
            assert json.loads(report)==json.loads(problem['validationReport'])
            cursor.execute('SELECT ordinal,input_data,expected_output,score,subtask_key,checker_type FROM test_cases WHERE problem_id=%s ORDER BY ordinal',(row['id'],))
            actual=cursor.fetchall()
            expected=[(i,c['input'],c['output'],c['score'],c.get('subtaskKey'),c.get('checkerType','TOKENS')) for i,c in enumerate(problem['testCases'],1)]
            assert list(actual)==expected,f'{code}: published test cases differ from verified pack'
            cursor.execute('SELECT subtask_key,label,score FROM problem_subtasks WHERE problem_id=%s ORDER BY subtask_key',(row['id'],))
            assert list(cursor.fetchall())==sorted((s['key'],s['label'],s['score']) for s in problem['subtasks'])
            database_checks.append(dict(problem=code,version=version,testPoints=len(actual),status='MATCH'))
print('PASS: published inputs, outputs, scores, subtasks and certificates match all three verified packs.',flush=True)
probes=json.loads((ROOT/'problem-packs/leakage-probes.json').read_text(encoding='utf-8'))
e2e.SESSION=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
username='qa_leakage_'+uuid.uuid4().hex[:12];password=os.environ['ADMIN_INITIAL_PASSWORD']
e2e.api('POST','/api/auth/register',dict(username=username,password=password),201)
e2e.api('POST','/api/auth/login',dict(username=username,password=password))
evidence=[]
for batch,selected in [
    ('202403',[(3,'no-pivot-row-swap',60,8)]),
    ('202609',[(4,'singleton-empty-graph-no-output',90,44),(5,'zero-updates-no-initial-answer',95,25)]),
]:
    problems=e2e.api('GET',f'/api/problems?batch={batch}&size=100')['items']
    exam=e2e.api('POST','/api/exams',dict(batch=batch),201)
    try:
        for position,name,wrong_score,points in selected:
            p=next(p for p in problems if p['code']==f'{batch}-{position}')
            source=(ROOT/f'problem-packs/{batch}/reference/{position}.cpp').read_text(encoding='utf-8')
            definition=next(d for d in probes if d['batch']==batch and d['position']==position and d['name']==name)
            wrong=source
            for before,after in definition['edits']:
                assert wrong.count(before)==1;wrong=wrong.replace(before,after,1)
            for label,code,status,score in [(name,wrong,'WA',wrong_score),('reference',source,'AC',100)]:
                result=e2e.submit(p['id'],code,exam['id'])
                assert result['status']==status,(p['code'],label,result['status'])
                assert result['score']==score,(p['code'],label,result['score'])
                assert len(result['results'])==points
                row=dict(problem=p['code'],test=label,submissionId=result['id'],status=result['status'],score=result['score'],testPoints=points,problemVersion=p['version'],examId=exam['id'])
                evidence.append(row);print(json.dumps(row),flush=True)
    finally:e2e.api('POST',f'/api/exams/{exam["id"]}/finish')
data['databaseVerification']=database_checks
data['liveApiRegression']=evidence
receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: all three formerly full-score wrong programs lose points; references remain AC/100.',flush=True)
