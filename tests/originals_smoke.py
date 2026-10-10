"""Submit every newly built original reference through the real API and Worker."""
import json
from e2e import api, submit, RESULTS

problems = sorted(api("GET", "/api/problems?batch=ORIGINAL&size=100")["items"], key=lambda p: p["code"])
assert [p["code"] for p in problems] == [f"LAB-{i:03d}" for i in range(1, 13)]
evidence = []
for p in problems:
    assert p["evaluationType"] == "FULL" and p["constructionStatus"] == "VERIFIED"
    source = api("GET", f"/api/admin/problems/{p['id']}/assets/reference.cpp")["content"]
    result = submit(p["id"], source)
    assert (result["status"], result["score"]) == ("AC", 100), p["code"]
    assert len(result["results"]) == 8
    assert all(r["stdout"] is None and r["stderr"] is None for r in result["results"])
    evidence.append({"code": p["code"], "submissionId": result["id"], "status": result["status"], "score": result["score"], "testPoints": 8})
    print(f"{p['code']}: AC 100 through live API/Worker", flush=True)
RESULTS.mkdir(parents=True, exist_ok=True)
(RESULTS / "originals-evidence.json").write_text(json.dumps({"passed": True, "problems": evidence}, ensure_ascii=False, indent=2), encoding="utf-8")
