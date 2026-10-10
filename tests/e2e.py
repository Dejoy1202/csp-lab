"""Live API integration tests using the platform's isolated judge."""
import argparse
import copy
import json
import os
from pathlib import Path
import time
import unittest
import urllib.error
import urllib.request
import uuid
import http.cookiejar
import subprocess

BASE=os.environ.get("BASE_URL","http://localhost:8080")
KEY=os.environ["API_KEY"]
PROJECT=os.environ.get("COMPOSE_PROJECT_NAME","csp-lab")
ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"test-results/windows" if os.name=="nt" else Path("/results")
SESSION=None
AC='#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}\n'

def api(method,path,data=None,expected=200,key=KEY):
    body=json.dumps(data,ensure_ascii=False).encode() if data is not None else None
    headers={"Content-Type":"application/json"}
    opener=SESSION if SESSION is not None and key==KEY else None
    if opener is None: headers["X-API-Key"]=key
    elif method not in ("GET","HEAD","OPTIONS"):
        with opener.open(BASE+"/api/auth/csrf",timeout=30) as csrf:
            headers["X-CSRF-TOKEN"]=json.load(csrf)["token"]
    req=urllib.request.Request(BASE+path,data=body,headers=headers,method=method)
    try:
        with (opener.open(req,timeout=120) if opener else urllib.request.urlopen(req,timeout=120)) as response:
            status=response.status; raw=response.read(); result=json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        status=error.code; result=json.load(error)
    assert status==expected, f"{method} {path}: expected {expected}, got {status}: {result}"
    return result

def wait_submission(submission,seconds=180):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        result=api("GET",f"/api/submissions/{submission}")
        if result["status"] not in ("QUEUED","RUNNING"):return result
        time.sleep(0.2)
    raise AssertionError(f"Submission {submission} did not finish")

def submit(problem,source=AC,exam=None,mode="JUDGE",wait=True):
    result=api("POST","/api/submissions" if mode=="JUDGE" else "/api/runs",{"problemId":problem,"sourceCode":source,"language":"CPP17","examId":exam},202)
    return wait_submission(result["id"],300) if wait else result

def fixture(code):
    return {"code":code,"title":"沙箱集成验收：整数相加","sourceYear":2024,"sourceBatch":"TEST","sourcePosition":1,"difficulty":"EASY","tags":["验收"],
            "timeLimitMs":250,"memoryLimitMb":64,"sourceUrl":None,"statement":"读入两个整数并输出和。原创测试题。","inputDescription":"两个整数", "outputDescription":"一行和",
            "evaluationType":"FULL","license":"CSP Lab original","samples":[{"input":"2 3\n","output":"5\n"}],
            "testCases":[{"input":a,"output":b,"score":25,"subtaskKey":None} for a,b in [("2 3\n","5\n"),("10 20\n","30\n"),("-4 2\n","-2\n"),("-8 -2\n","-10\n")]],
            "constructionStatus":"VERIFIED","constraintsDescription":"|a|,|b| <= 100","scoringNotes":"4 independent cases of 25 points","outputLimitKb":64,"subtasks":[],"assets":[],"validationReport":"{\"status\":\"VERIFIED\",\"originalFixture\":true}"}

def service(name):
    if os.name=="nt":
        assert name=="worker"
        class WindowsWorker:
            def invoke(self,*args):
                subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(ROOT/"scripts/restart-worker-windows.ps1"),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
            def kill(self,signal=None):self.invoke("-StopOnly")
            def start(self):self.invoke()
        return WindowsWorker()
    import docker
    return docker.from_env().containers.list(all=True,filters={"label":["com.docker.compose.project="+PROJECT,"com.docker.compose.service="+name]})[0]

def sql(query):
    if os.name=="nt":
        import pymysql
        with pymysql.connect(host=os.environ['DB_HOST'],port=int(os.environ.get('DB_PORT','3306')),user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ['DB_NAME'],charset='utf8mb4',autocommit=True) as db:
            with db.cursor() as cursor:
                cursor.execute(query)
                return '\n'.join('\t'.join(str(value) for value in row) for row in cursor.fetchall())
    mysql=service("mysql")
    env=dict(pair.split("=",1) for pair in mysql.attrs["Config"]["Env"] if "=" in pair)
    result=mysql.exec_run(["mysql","-N","-B","-u"+env["MYSQL_USER"],env["MYSQL_DATABASE"],"-e",query],environment={"MYSQL_PWD":env["MYSQL_PASSWORD"]})
    assert result.exit_code==0, "Test database operation failed"
    return result.output.decode()

def test_account(username=None):
    """Use a separate QA account; never finish or modify the owner's active exam."""
    global SESSION
    SESSION=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    password=os.environ["ADMIN_INITIAL_PASSWORD"]
    if username is None:
        username="qa_e2e_"+uuid.uuid4().hex[:16]
        account=api("POST","/api/auth/register",{"username":username,"password":password},201)
        # Privileged test setup promotes only the newly registered random fixture.
        sql(f"UPDATE users SET role='ADMIN' WHERE id={int(account['id'])} AND username='{username}' AND role='USER'")
    assert api("POST","/api/auth/login",{"username":username,"password":password})["role"]=="ADMIN"
    return username

class LiveTests(unittest.TestCase):
    evidence=[]
    @classmethod
    def setUpClass(cls):
        cls.username=test_account()
        cls.prefix="IT-"+uuid.uuid4().hex[:8]
        cls.problem=api("POST","/api/admin/problems",fixture(cls.prefix),201)["id"]
        cls.csp=api("GET","/api/problems?batch=202403&size=100")["items"]
        cls.csp=sorted([p for p in cls.csp if p["code"].startswith("202403-")],key=lambda p:p["sourcePosition"])
        assert len(cls.csp)==5,"Build/import the five verified 202403 packs first"
    def record(self,label,result):
        self.evidence.append({"test":label,"submissionId":result["id"],"status":result["status"],"score":result["score"],"testPoints":len(result["results"])})
    def check(self,label,source,status,score):
        result=submit(self.problem,source);self.assertEqual(result["status"],status);self.assertEqual(result["score"],score)
        self.record(label,result);return result
    def test_01_auth_health_and_full_metadata(self):
        api("GET","/actuator/health",key="")
        api("GET","/api/problems",expected=401,key="wrong")
        for p in self.csp:
            detail=api("GET",f"/api/problems/{p['id']}")
            self.assertEqual(detail["constructionStatus"],"VERIFIED")
            self.assertEqual(detail["evaluationType"],"FULL")
            self.assertTrue(detail["statement"] and detail["constraintsDescription"] and detail["scoringNotes"])
            self.assertTrue(detail["scoring"])
            self.assertFalse(any("inputData" in row or "expectedOutput" in row for row in detail["scoring"]))
    def test_02_ac(self):self.check("AC",AC,"AC",100)
    def test_03_wa(self):self.check("WA","int main(){return 0;}","WA",0)
    def test_04_ce(self):
        result=self.check("CE","int main( { this is invalid; }","CE",0)
        self.assertTrue(result["compileOutput"])
    def test_05_tle(self):self.check("TLE","int main(){volatile unsigned x=0;for(;;)++x;}","TLE",0)
    def test_06_mle(self):self.check("MLE",'#include <cstdlib>\n#include <cstring>\nint main(){for(;;){auto p=malloc(1024*1024);if(!p)return 1;memset(p,1,1024*1024);asm volatile(""::"r"(p):"memory");}}',"MLE",0)
    def test_07_re(self):self.check("RE",'#include <csignal>\nint main(){raise(SIGSEGV);}',"RE",0)
    def test_08_partial(self):self.check("PARTIAL",'#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;if(a>=0)std::cout<<a+b;}',"WA",50)
    def test_09_output_limit(self):self.check("OLE",'#include <cstdio>\nint main(){for(;;)puts("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx");}',"OLE",0)
    def test_10_samples_do_not_award_points_or_leak_hidden_outputs(self):
        sample=submit(self.problem,AC,mode="SAMPLE");self.assertEqual(sample["status"],"AC");self.assertEqual(sample["score"],0)
        self.assertEqual(sample["results"][0]["stdout"].strip(),"5")
        hidden=submit(self.problem,'#include <iostream>\nint main(){std::cerr<<"hidden-input-echo";}')
        self.assertTrue(all(r["stdout"] is None and r["stderr"] is None for r in hidden["results"]))
    def test_11_drafts_unicode_conflict_and_versions(self):
        path=f"/api/problems/{self.problem}/draft"
        before=api("GET",path);saved=api("PUT",path,{"sourceCode":AC+"// 中文自动保存\n","revision":before["revision"]})
        self.assertEqual(saved["revision"],before["revision"]+1);self.assertIn("中文",saved["sourceCode"])
        api("PUT",path,{"sourceCode":"stale","revision":before["revision"]},409)
        history=api("GET",f"/api/submissions?problemId={self.problem}&size=100")
        self.assertGreaterEqual(history["total"],9)
        detail=api("GET",f"/api/submissions/{history['items'][0]['id']}");self.assertIn("sourceCode",detail)
    def test_12_paper_catalog(self):
        papers=api("GET","/api/papers")
        self.assertEqual(len(papers),44)
        self.assertEqual(sum(len(p["problems"]) for p in papers),220)
        self.assertTrue(api("GET","/api/papers/201312")["ready"])
        self.assertTrue(api("GET","/api/papers/202403")["ready"])
    def test_13_building_sample_only_and_atomic_batch(self):
        p=fixture(self.prefix+"-BUILD");p.update(constructionStatus="BUILDING",testCases=[])
        building=api("POST","/api/admin/problems",p,201)["id"]
        api("POST","/api/submissions",{"problemId":building,"sourceCode":AC,"language":"CPP17","examId":None},400)
        p=fixture(self.prefix+"-SAMPLE");p.update(evaluationType="SAMPLE_ONLY",testCases=[])
        sample=api("POST","/api/admin/problems",p,201)["id"]
        api("POST","/api/submissions",{"problemId":sample,"sourceCode":AC,"language":"CPP17","examId":None},400)
        self.assertEqual(submit(sample,AC,mode="SAMPLE")["score"],0)
        first=fixture(self.prefix+"-ROLLBACK");duplicate=fixture(self.prefix)
        api("POST","/api/admin/problems/batch",{"problems":[first,duplicate]},409)
        self.assertFalse(any(p["code"]==first["code"] for p in api("GET","/api/problems?size=100")["items"]))
    def test_14_bundled_partial_scoring(self):
        p=fixture(self.prefix+"-GROUP");p["subtasks"]=[{"key":"positive","label":"正数","score":40},{"key":"negative","label":"负数","score":60}]
        for i,c in enumerate(p["testCases"]):c.update(score=0,subtaskKey="positive" if i<2 else "negative")
        id=api("POST","/api/admin/problems",p,201)["id"]
        result=submit(id,'#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;if(a>=0)std::cout<<a+b;}')
        self.assertEqual(result["score"],40);self.assertEqual([g["score"] for g in result["subtasks"]],[0,40])
        self.record("BUNDLED_PARTIAL",result)
    def test_15_four_hour_five_problem_exam_and_review(self):
        ids=[p["id"] for p in self.csp]
        api("POST","/api/exams",{"title":"invalid","problemIds":[ids[0]]*5},400)
        exam=api("POST","/api/exams",{"title":"2024-03 第33次 本站模拟验收","problemIds":ids},201)
        self.assertEqual(exam["durationSeconds"],14400);self.assertEqual(exam["maxScore"],500)
        self.assertGreater(exam["remainingSeconds"],14390)
        api("POST","/api/exams",{"title":"second","problemIds":ids},409)
        api("POST","/api/submissions",{"problemId":self.problem,"sourceCode":AC,"language":"CPP17","examId":exam["id"]},400)
        for i,p in enumerate(self.csp,1):
            source=(ROOT/f"problem-packs/202403/reference/{i}.cpp" if os.name=="nt" else Path(f"/app/reference/{i}.cpp")).read_text(encoding="utf-8")
            result=submit(p["id"],source,exam=exam["id"])
            self.assertEqual((result["status"],result["score"]),("AC",100));self.record(f"CSP_T{i}",result)
        # Highest score survives a later wrong submission.
        submit(ids[0],"int main(){return 0;}",exam=exam["id"])
        finished=api("POST",f"/api/exams/{exam['id']}/finish")
        self.assertEqual(finished["totalScore"],500);self.assertEqual(finished["status"],"FINISHED")
        api("POST","/api/submissions",{"problemId":ids[0],"sourceCode":AC,"language":"CPP17","examId":exam["id"]},409)
        self.assertEqual(api("GET",f"/api/submissions?examId={exam['id']}&size=100")["total"],6)
        self.__class__.exam_id=exam["id"]
    def test_16_server_enforces_expiration(self):
        exam=api("POST","/api/exams",{"title":"期限验收","problemIds":[p["id"] for p in self.csp]},201)
        sql(f"UPDATE mock_exams SET ends_at=DATE_SUB(NOW(6),INTERVAL 1 SECOND) WHERE id={exam['id']}")
        result=api("GET",f"/api/exams/{exam['id']}");self.assertEqual(result["status"],"FINISHED");self.assertEqual(result["remainingSeconds"],0)
        api("POST","/api/submissions",{"problemId":self.csp[0]["id"],"sourceCode":AC,"language":"CPP17","examId":exam["id"]},409)
    def test_17_sandbox_network_process_and_filesystem_enforcement(self):
        source='#include <iostream>\n#include <unistd.h>\n#include <sys/socket.h>\n#include <fcntl.h>\n#include <cerrno>\nint main(){ if(fork()!=-1||errno!=EPERM)return 1; if(socket(AF_INET,SOCK_STREAM,0)!=-1||errno!=EPERM)return 2; if(open("/sandbox/run.py",O_WRONLY)!=-1)return 3; if(access("/var/run/docker.sock",F_OK)==0)return 4; long long a,b;std::cin>>a>>b;std::cout<<a+b;}\n'
        if os.name=="nt":
            source='#include <windows.h>\n#include <fstream>\n#include <iostream>\n#include <cstdlib>\nint main(){HANDLE token;DWORD value=0,size=0;if(!OpenProcessToken(GetCurrentProcess(),TOKEN_QUERY,&token))return 1;GetTokenInformation(token,TokenIsAppContainer,&value,sizeof(value),&size);CloseHandle(token);if(value!=1||getenv("DB_PASSWORD")||getenv("API_KEY"))return 2;std::ofstream f("forbidden.txt");if(f.good())return 3;long long a,b;std::cin>>a>>b;std::cout<<a+b;}'
        self.check("ISOLATION",source,"AC",100)
    def test_18_worker_crash_recovers_with_lease(self):
        queued=submit(self.problem,"int main(){for(;;){}}",wait=False)
        worker=service("worker");deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            if api("GET",f"/api/submissions/{queued['id']}")["status"]=="RUNNING":break
            time.sleep(.05)
        worker.kill(signal="SIGKILL")
        sql(f"UPDATE submissions SET lease_until=DATE_SUB(NOW(6),INTERVAL 1 SECOND) WHERE id={queued['id']} AND status='RUNNING'")
        worker.start()
        result=wait_submission(queued["id"])
        self.assertEqual(result["status"],"TLE");self.assertGreaterEqual(result["attempts"],2);self.record("LEASE_RECOVERY",result)
    def test_19_problem_versions_and_edit_guard(self):
        p=fixture(self.prefix+"-VERSION");pid=api("POST","/api/admin/problems",p,201)["id"]
        original=api("GET",f"/api/problems/{pid}/versions/1");p["title"]="修改后的题目"
        api("PUT",f"/api/admin/problems/{pid}",p)
        self.assertEqual(api("GET",f"/api/problems/{pid}")["version"],2)
        self.assertEqual(api("GET",f"/api/problems/{pid}/versions/1")["title"],original["title"])
        self.assertEqual(api("GET",f"/api/problems/{pid}/versions/2")["title"],"修改后的题目")
        queued=submit(pid,"int main(){for(;;){}}",wait=False)
        api("PUT",f"/api/admin/problems/{pid}",p,409)
        wait_submission(queued["id"])
    @classmethod
    def tearDownClass(cls):
        RESULTS.mkdir(parents=True,exist_ok=True)
        report={"backend":"Spring Boot/JDK21/MySQL8","liveDocker":os.name!='nt',"sandbox":"Windows AppContainer + Job Object" if os.name=='nt' else 'Docker',"evidence":cls.evidence}
        (RESULTS/"e2e-evidence.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        snapshot={"testUsername":cls.username,"problemId":cls.problem,"examId":getattr(cls,"exam_id",None),"submissions":api("GET",f"/api/submissions?problemId={cls.problem}&size=100"),"draft":api("GET",f"/api/problems/{cls.problem}/draft")}
        (RESULTS/"persistence-before.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")

def persistence():
    before=json.loads((RESULTS/"persistence-before.json").read_text(encoding="utf-8"));pid=before["problemId"]
    test_account(before["testUsername"])
    assert api("GET",f"/api/submissions?problemId={pid}&size=100")==before["submissions"]
    assert api("GET",f"/api/problems/{pid}/draft")==before["draft"]
    assert api("GET",f"/api/exams/{before['examId']}")["totalScore"]==500
    report={"status":"PASS","verifiedAfterComposeDownUp":os.name!='nt',"verifiedAfterWindowsRestart":os.name=='nt',"submissionCount":before["submissions"]["total"],"examScore":500,"draftPreserved":True}
    (RESULTS/"persistence-after.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--persistence",action="store_true");args=parser.parse_args()
    if args.persistence:persistence()
    else:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(LiveTests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        RESULTS.mkdir(parents=True,exist_ok=True)
        (RESULTS/"e2e-summary.json").write_text(json.dumps({"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"passed":result.wasSuccessful()},indent=2),encoding="utf-8")
        raise SystemExit(0 if result.wasSuccessful() else 1)
