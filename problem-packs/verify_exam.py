"""Exercise five-question papers through an ordinary account and real Judge Worker."""
import argparse
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import time
import urllib.request
import urllib.error

BASE=os.environ.get('BASE_URL','http://backend:8080')
ROOT=Path(__file__).resolve().parent
SESSION=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

def api(method,path,data=None,expected=200):
    headers={'Content-Type':'application/json'}
    if method!='GET':
        headers['X-CSRF-TOKEN']=api('GET','/api/auth/csrf')['token']
    request=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),headers=headers,method=method)
    try:
        with SESSION.open(request,timeout=120) as response:
            status=response.status;raw=response.read();result=json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        status=error.code;result=json.load(error)
    assert status==expected,f'{method} {path}: expected {expected}, got {status}: {result}'
    return result

def submit(exam,index,source,sample=False):
    return api('POST','/api/runs' if sample else '/api/submissions',dict(problemId=exam['problems'][index]['problemId'],examId=exam['id'],language='CPP17',sourceCode=source),202)['id']

def wait(identifier,deadline):
    while time.monotonic()<deadline:
        result=api('GET',f'/api/submissions/{identifier}')
        if result['status'] not in ('QUEUED','RUNNING'):return result
        time.sleep(.5)
    raise AssertionError(f'Submission {identifier} did not finish')

def check(batch,output):
    paper=api('GET',f'/api/papers/{batch}')
    assert paper['ready'] and len(paper['problems'])==5
    exam=api('POST','/api/exams',{'batch':batch},201)
    assert exam['durationSeconds']==14400 and exam['maxScore']==500 and len(exam['problems'])==5
    evidence=[]
    try:
        sources=[(ROOT/batch/f'reference/{i}.cpp').read_text(encoding='utf-8') for i in range(1,6)]
        # Queue all five; the independent worker uses the platform sandbox.
        identifiers=[submit(exam,i,source) for i,source in enumerate(sources)]
        deadline=time.monotonic()+900
        for i,identifier in enumerate(identifiers,1):
            result=wait(identifier,deadline)
            assert (result['status'],result['score'])==('AC',100),f'{batch} T{i}: {result["status"]}, {result["score"]}'
            assert all(row.get('stdout') is None and row.get('stderr') is None for row in result['results'])
            evidence.append(dict(problem=f'{batch}-{i}',submissionId=identifier,status=result['status'],score=result['score'],testPoints=len(result['results'])))
            print(f'{batch} T{i}: real worker AC / 100 ({len(result["results"])} points)',flush=True)
        sample=wait(submit(exam,0,sources[0],True),time.monotonic()+60)
        assert sample['status']=='AC' and sample['score']==0
        mutations=json.loads((ROOT/batch/'mutations.json').read_text(encoding='utf-8'))
        selected=next(m for m in mutations if m['position']==1)
        wrong=sources[0]
        for before,after in selected['edits']:wrong=wrong.replace(before,after,1)
        partial=wait(submit(exam,0,wrong),time.monotonic()+300)
        assert partial['status']=='WA' and 0<partial['score']<100
        print(f'{batch} partial-score witness: WA / {partial["score"]}',flush=True)
        construction=None
        if batch=='202609':
            plan_source=sources[3]
            empty=plan_source.replace("cout<<groups[i].size();for(long long x:groups[i])cout<<' '<<x;","cout<<0;")
            counted=wait(submit(exam,3,empty),time.monotonic()+600)
            assert counted['status']=='WA' and counted['score']==40
            alternative=plan_source.replace("for(long long x:groups[i])", "reverse(groups[i].begin(),groups[i].end());for(long long x:groups[i])")
            different=wait(submit(exam,3,alternative),time.monotonic()+600)
            assert different['status']=='AC' and different['score']==100
            construction=dict(countOnlyScore=40,countOnlySubmissionId=counted['id'],alternativePlanStatus='AC',alternativeSubmissionId=different['id'])
            print('202609 construction grading: count-only 40; alternative valid plan AC / 100',flush=True)
        extra_witnesses=[]
        config=ROOT/batch/'exam-witnesses.json'
        if config.exists():
            for definition in json.loads(config.read_text(encoding='utf-8')):
                index=definition['position']-1
                witness_source=definition.get('sourceCode',sources[index])
                for before,after in definition.get('edits',[]):
                    assert witness_source.count(before)==1,definition['label']
                    witness_source=witness_source.replace(before,after,1)
                judged=wait(submit(exam,index,witness_source),time.monotonic()+600)
                assert (judged['status'],judged['score'])==(definition['expectedStatus'],definition['expectedScore']),(definition,judged['status'],judged['score'])
                extra_witnesses.append(dict(label=definition['label'],problem=f'{batch}-{index+1}',submissionId=judged['id'],status=judged['status'],score=judged['score']))
                print(f'{batch} {definition["label"]}: {judged["status"]} / {judged["score"]}',flush=True)
        finished=api('POST',f'/api/exams/{exam["id"]}/finish')
        assert finished['status']=='FINISHED' and finished['totalScore']==500
        assert api('GET',f'/api/exams/{exam["id"]}')['totalScore']==500
        api('POST','/api/submissions',dict(problemId=exam['problems'][0]['problemId'],examId=exam['id'],language='CPP17',sourceCode=sources[0]),409)
        report=dict(batch=batch,status='PASS',ordinaryAccount=True,liveDocker=os.name!='nt',sandbox='Windows AppContainer + Job Object' if os.name=='nt' else 'Docker',examId=exam['id'],durationSeconds=14400,totalScore=500,
            sampleScore=0,construction=construction,extraWitnesses=extra_witnesses,partialScore=partial['score'],partialSubmissionId=partial['id'],highestScorePreserved=True,evidence=evidence)
        output.mkdir(parents=True,exist_ok=True)
        (output/(batch+'-exam-evidence.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'{batch}: five-question exam finished 500 / 500',flush=True)
    finally:
        if api('GET',f'/api/exams/{exam["id"]}')['status']=='RUNNING':api('POST',f'/api/exams/{exam["id"]}/finish')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batches',required=True);parser.add_argument('--output',default='/output');args=parser.parse_args()
    username='qa_paper_'+secrets.token_hex(8)
    api('POST','/api/auth/register',dict(username=username,password=secrets.token_urlsafe(24)),201)
    for batch in args.batches.split(','):
        assert len(batch)==6 and batch.isdigit()
        check(batch,Path(args.output))
