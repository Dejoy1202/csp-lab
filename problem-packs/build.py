"""Build and verify packs, isolating every reference compilation/run."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request
import urllib.parse
import uuid
from sandbox import Sandbox, tokens
from mutations import verify_mutations

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"202403"))
from generator import dataset, small_cases, SEED
from oracles import ORACLES
from validators import validate

def large_water_expected(data):
    it=iter(map(int,data.split()));c,m,n=next(it),next(it),next(it)
    water={next(it):next(it) for _ in range(m)};ops=[next(it) for _ in range(n)]
    positions=sorted(water)
    if set(water.values())=={4}:
        assert n==1 and ops[0]==positions[0]
        return "0\n"
    assert set(water.values())=={1} and n==3*m+1 and ops[-1]==positions[0]
    assert ops[:-1]==[p for p in positions for _ in range(3)]
    return f"{m}\n"*(3*m)+"0\n"

def expected(position,data):
    if position==4 and int(data.split(maxsplit=3)[1])>3000:
        return large_water_expected(data)
    return ORACLES[position](data)

def verify_run(sandbox,binary,position,data,limit_ms,memory_mb):
    output=expected(position,data)
    result=sandbox.run(binary,data,limit_ms,memory_mb)
    assert result["status"]=="OK", f"T{position}: reference {result['status']}"
    assert tokens(result["stdout"].encode())==tokens(output.encode()), f"T{position}: reference/oracle mismatch"
    return output,result

def import_file(path):
    pack=json.loads(gzip.decompress(path.read_bytes()))
    problem=pack["problems"][0]
    query=urllib.parse.urlencode({"batch":problem["sourceBatch"],"size":100})
    req=urllib.request.Request(os.environ.get("BASE_URL","http://backend:8080")+"/api/problems?"+query,headers={"X-API-Key":os.environ["API_KEY"]})
    with urllib.request.urlopen(req,timeout=30) as response:existing=json.load(response)["items"]
    match=next((p for p in existing if p["code"]==problem["code"]),None)
    if match:
        if match["constructionStatus"]=="VERIFIED":return {"id":match["id"],"skippedExisting":True}
        req=urllib.request.Request(os.environ.get("BASE_URL","http://backend:8080")+"/api/admin/problems/"+str(match["id"]),data=json.dumps(problem,ensure_ascii=False).encode("utf-8"),headers={"X-API-Key":os.environ["API_KEY"],"Content-Type":"application/json"},method="PUT")
        with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)
    boundary="csp-pack-"+uuid.uuid4().hex
    body=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\nContent-Type: application/gzip\r\n\r\n".encode()+path.read_bytes()+f"\r\n--{boundary}--\r\n".encode())
    req=urllib.request.Request(os.environ.get("BASE_URL","http://backend:8080")+"/api/admin/problems/import-pack",data=body,
        headers={"X-API-Key":os.environ["API_KEY"],"Content-Type":"multipart/form-data; boundary="+boundary},method="POST")
    with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)

def build(output,import_now,positions):
    assert positions and set(positions)<=set(range(1,6)), 'Invalid problem positions'
    output.mkdir(parents=True,exist_ok=True)
    sandbox=Sandbox(os.environ.get("SANDBOX_IMAGE","csp-lab-sandbox:local"),"pack-build-"+uuid.uuid4().hex)
    problems=json.loads((ROOT/"202403/statements.json").read_text(encoding="utf-8"))
    reports=[];completed=[]
    for position,problem in enumerate(problems,1):
        if position not in positions:continue
        print(f"T{position}: compiling reference inside the isolated sandbox",flush=True)
        source=(ROOT/f"202403/reference/{position}.cpp").read_text(encoding="utf-8")
        binary,diagnostic=sandbox.compile(source)
        assert binary is not None,diagnostic
        for sample in problem["samples"]:
            validate(position,sample["input"])
            answer,result=verify_run(sandbox,binary,position,sample["input"],problem["timeLimitMs"],problem["memoryLimitMb"])
            assert tokens(answer.encode())==tokens(sample["output"].encode()),"Invalid hand-authored sample"
        small_count=0
        for data in small_cases(position):
            validate(position,data)
            verify_run(sandbox,binary,position,data,problem["timeLimitMs"],problem["memoryLimitMb"])
            small_count+=1
        print(f"T{position}: {small_count} independent small-case checks passed; building boundary cases",flush=True)
        cases,subtasks=dataset(position)
        tests=[];case_reports=[]
        for i,(data,group,score) in enumerate(cases,1):
            validate(position,data,group)
            answer,result=verify_run(sandbox,binary,position,data,problem["timeLimitMs"],problem["memoryLimitMb"])
            tests.append({"input":data,"output":answer,"score":score,"subtaskKey":group})
            case_reports.append({"ordinal":i,"subtaskKey":group,"inputBytes":len(data.encode()),"outputBytes":len(answer.encode()),
                                 "inputSha256":hashlib.sha256(data.encode()).hexdigest(),"outputSha256":hashlib.sha256(answer.encode()).hexdigest(),
                                 "referenceTimeMs":result["time_ms"],"referenceMemoryKb":result["memory_kb"]})
            print(f"T{position} case {i}/{len(cases)} passed ({result['time_ms']} ms)",flush=True)
        report={"problem":problem["code"],"seed":SEED,"reference":"independently authored C++17",
                "oracle":"independent Python; exact rational rank for T3; analytical large wave for T4",
                "smallDifferentialCases":small_count,"samplesVerified":len(problem["samples"]),"cases":case_reports,
                "officialHiddenData":False,"scoringType":"SITE_SIMULATION","status":"VERIFIED"}
        problem.update(evaluationType="FULL",constructionStatus="VERIFIED",license="CSP Lab independently worded specification and generated data; original CCF title/rules attributed; not an official licensed statement copy",
                       outputLimitKb=16384,testCases=tests,subtasks=subtasks,validationReport=json.dumps(report,ensure_ascii=False),assets=[])
        for filename,kind in [(f"reference/{position}.cpp","REFERENCE"),("generator.py","GENERATOR"),("validators.py","VALIDATOR"),("oracles.py","VALIDATOR")]:
            problem["assets"].append({"name":filename.replace("/","-"),"kind":kind,"content":(ROOT/"202403"/filename).read_text(encoding="utf-8")})
        path=output/f"202403-{position}.json.gz"
        # Keep gzip headers deterministic; data checksums are reproducible with SEED.
        content=json.dumps({"problems":[problem]},ensure_ascii=False,separators=(",",":")).encode("utf-8")
        completed.append((path,gzip.compress(content,compresslevel=6,mtime=0)))
        reports.append(report)
        del tests,content,cases
    # A missed known error must not replace a verified pack or reach the DB.
    mutation_report=verify_mutations('202403',problems,sandbox,positions)
    for path,content in completed:path.write_bytes(content)
    suffix='-'.join(map(str,sorted(set(positions))))
    mutation_path=output/('202403-mutations.json' if set(positions)==set(range(1,6)) else f'202403-mutations-positions-{suffix}.json')
    mutation_path.write_text(json.dumps(mutation_report,ensure_ascii=False,indent=2),encoding='utf-8')
    if import_now:
        for path,_ in completed:print(f"Imported {path.name}: {import_file(path)}",flush=True)
    reports=[]
    for position in range(1,6):
        path=output/f"202403-{position}.json.gz"
        if path.exists():
            packed=json.loads(gzip.decompress(path.read_bytes()))
            reports.append(json.loads(packed["problems"][0]["validationReport"]))
    (output/"validation-report.json").write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(reports)}/5 verified packs are ready.",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--import",dest="import_now",action="store_true")
    parser.add_argument("--output",default="/output")
    parser.add_argument("--positions",type=int,nargs="+",default=list(range(1,6)))
    parser.add_argument("--import-existing",action="store_true")
    args=parser.parse_args()
    if args.import_existing:
        for path in sorted(Path(args.output).glob("[0-9]*-[1-5].json.gz")):
            print(f"Imported {path.name}: {import_file(path)}",flush=True)
    else:build(Path(args.output),args.import_now,args.positions)
