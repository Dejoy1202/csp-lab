"""A durable MySQL task queue with SKIP LOCKED, expiring leases and fencing."""
import logging
import base64
import os
import signal
import threading
import time
import uuid
import pymysql
from sandbox import Sandbox
from checkers import check_output
from scoring import score_results

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
STOP = threading.Event()
WORKER_ID = uuid.uuid4().hex
POLL = float(os.environ.get("WORKER_POLL_SECONDS", "0.5"))

def utf8_excerpt(text):
    return text.encode("utf-8")[:32768].decode("utf-8","ignore")

def connection():
    return pymysql.connect(host=os.environ.get("DB_HOST", "mysql"), user=os.environ["DB_USER"],
                           password=os.environ["DB_PASSWORD"], database=os.environ.get("DB_NAME", "csp_lab"),
                           port=int(os.environ.get("DB_PORT", "3306")),
                           charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
                           init_command="SET time_zone = '+08:00'", autocommit=False,
                           connect_timeout=10, read_timeout=30, write_timeout=30)

def claim():
    with connection() as db:
        with db.cursor() as cur:
            cur.execute("SELECT id,worker_id,attempts FROM submissions WHERE status='QUEUED' OR (status='RUNNING' AND lease_until<NOW(6)) ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED")
            row = cur.fetchone()
            if not row:
                db.commit()
                return None
            # Every attempt uses a unique token; old attempts cannot commit results.
            token = WORKER_ID + "-" + uuid.uuid4().hex[:16]
            if row["attempts"] >= 3:
                cur.execute("UPDATE submissions SET status='SYSTEM_ERROR',system_message='Worker retries exhausted',finished_at=NOW(6),lease_until=NULL WHERE id=%s", (row["id"],))
                db.commit()
                return {"cleanup": row["worker_id"]}
            cur.execute("UPDATE submissions SET status='RUNNING',worker_id=%s,attempts=attempts+1,started_at=NOW(6),lease_until=DATE_ADD(NOW(6),INTERVAL 60 SECOND) WHERE id=%s", (token, row["id"]))
            cur.execute("SELECT s.*,p.time_limit_ms,p.memory_limit_mb,p.output_limit_kb FROM submissions s JOIN problems p ON p.id=s.problem_id WHERE s.id=%s", (row["id"],))
            job = cur.fetchone()
            db.commit()
            job["previous_owner"] = row["worker_id"]
            return job

def heartbeat(job, done):
    while not done.wait(10):
        try:
            with connection() as db:
                with db.cursor() as cur:
                    cur.execute("UPDATE submissions SET lease_until=DATE_ADD(NOW(6),INTERVAL 60 SECOND) WHERE id=%s AND worker_id=%s AND status='RUNNING'", (job["id"], job["worker_id"]))
                db.commit()
        except Exception:
            logging.exception("Lease heartbeat failed for submission %s", job["id"])

def test_metadata(job):
    with connection() as db:
        with db.cursor() as cur:
            if job["mode"] == "SAMPLE":
                cur.execute("SELECT id,ordinal,0 AS score,NULL AS subtask_key FROM problem_samples WHERE problem_id=%s ORDER BY ordinal", (job["problem_id"],))
            else:
                cur.execute("SELECT id,ordinal,score,subtask_key FROM test_cases WHERE problem_id=%s ORDER BY ordinal", (job["problem_id"],))
            cases = cur.fetchall()
            cur.execute("SELECT subtask_key,score FROM problem_subtasks WHERE problem_id=%s ORDER BY subtask_key", (job["problem_id"],))
            return cases, cur.fetchall() if job["mode"] == "JUDGE" else []

def load_case(job, case):
    table = "problem_samples" if job["mode"] == "SAMPLE" else "test_cases"
    with connection() as db:
        with db.cursor() as cur:
            cur.execute("SELECT input_data,expected_output,checker_type FROM " + table + " WHERE id=%s", (case["id"],))
            return cur.fetchone()

def judge(job, sandbox):
    binary, diagnostic = sandbox.compile(job["source_code"])
    if binary is None:
        return "CE", 0, diagnostic, [], []
    cases, subtasks = test_metadata(job)
    if not cases:
        raise RuntimeError("No evaluation cases")
    results = []
    for case in cases:
        data = load_case(job, case)
        report = sandbox.run(binary, data["input_data"], job["time_limit_ms"], job["memory_limit_mb"], job["output_limit_kb"])
        if report["status"] == "SYSTEM_ERROR":
            raise RuntimeError("Sandbox enforcement unavailable")
        # Do not decode before comparison: reject invalid UTF-8 answers.
        if report["status"] == "OK":
            raw_output=base64.b64decode(report["stdout_b64"],validate=True)
            report["status"] = "AC" if check_output(data["checker_type"],data["input_data"],data["expected_output"],raw_output) else "WA"
        results.append({"ordinal": case["ordinal"], "status": report["status"],
                        "score": case["score"] if report["status"] == "AC" else 0,
                        "max_score": case["score"], "subtask_key": case["subtask_key"],
                        "time_ms": report["time_ms"], "memory_kb": report["memory_kb"],
                        "exit_code": report.get("exit_code"),
                        "message": {"AC":"Accepted", "WA":"Output or construction is invalid", "TLE":"Time limit exceeded", "MLE":"Memory limit exceeded", "OLE":"Combined output limit exceeded", "RE":f"Program exited with code {report.get('exit_code')}"}.get(report["status"],""),
                        "stdout": utf8_excerpt(report["stdout"]) if job["mode"] == "SAMPLE" else None,
                        "stderr": utf8_excerpt(report["stderr"]) if job["mode"] == "SAMPLE" else None})
    status, score, groups = score_results(results, subtasks)
    return status, score, diagnostic, results, groups

def complete(job, outcome):
    status, score, diagnostic, results, groups = outcome
    with connection() as db:
        with db.cursor() as cur:
            cur.execute("SELECT worker_id,status FROM submissions WHERE id=%s FOR UPDATE", (job["id"],))
            current = cur.fetchone()
            if current["worker_id"] != job["worker_id"] or current["status"] != "RUNNING":
                db.rollback()
                return
            cur.execute("DELETE FROM submission_results WHERE submission_id=%s", (job["id"],))
            cur.execute("DELETE FROM submission_subtasks WHERE submission_id=%s", (job["id"],))
            for r in results:
                cur.execute("INSERT INTO submission_results(submission_id,ordinal,status,score,max_score,time_ms,memory_kb,stdout,stderr,subtask_key,exit_code,message) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (job["id"], r["ordinal"], r["status"], r["score"], r["max_score"], r["time_ms"], r["memory_kb"], r["stdout"], r["stderr"], r["subtask_key"],r["exit_code"],r["message"]))
            for g in groups:
                cur.execute("INSERT INTO submission_subtasks(submission_id,subtask_key,status,score,max_score) VALUES(%s,%s,%s,%s,%s)", (job["id"], g["subtask_key"], g["status"], g["score"], g["max_score"]))
            cur.execute("UPDATE submissions SET status=%s,score=%s,compile_output=%s,system_message=NULL,finished_at=NOW(6),lease_until=NULL WHERE id=%s", (status, score, utf8_excerpt(diagnostic), job["id"]))
        db.commit()

def retry(job):
    with connection() as db:
        with db.cursor() as cur:
            cur.execute("UPDATE submissions SET status='QUEUED',lease_until=NULL,system_message='Infrastructure failure; retrying' WHERE id=%s AND worker_id=%s AND status='RUNNING'", (job["id"], job["worker_id"]))
        db.commit()

def main():
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: STOP.set())
    sandbox = Sandbox(os.environ.get("SANDBOX_IMAGE", "csp-lab-sandbox:local"), WORKER_ID)
    logging.info("Judge worker ready; %s sandbox", "Windows AppContainer/Job Object" if os.name == "nt" else "Docker cgroup v2/seccomp")
    while not STOP.is_set():
        try:
            job = claim()
            if not job:
                STOP.wait(POLL)
                continue
            if "cleanup" in job:
                if job["cleanup"]:
                    sandbox.cleanup_owner(job["cleanup"])
                continue
            if job["previous_owner"]:
                sandbox.cleanup_owner(job["previous_owner"])
            sandbox.owner = job["worker_id"]
            done = threading.Event()
            lease = threading.Thread(target=heartbeat, args=(job, done), daemon=True)
            lease.start()
            try:
                complete(job, judge(job, sandbox))
                logging.info("Submission %s completed", job["id"])
            except Exception:
                logging.exception("Submission %s infrastructure failure", job["id"])
                retry(job)
            finally:
                done.set()
                lease.join(timeout=2)
                sandbox.cleanup_owner(job["worker_id"])
        except Exception:
            logging.exception("Worker loop failed")
            STOP.wait(3)

if __name__ == "__main__":
    main()
