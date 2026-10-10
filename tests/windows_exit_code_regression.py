"""Exercise a real sandbox crash and persist its unsigned Windows code."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'worker'))
from windows_sandbox import WindowsSandbox
from worker import connection

sandbox = WindowsSandbox(owner='exit-code-regression')
binary, diagnostic = sandbox.compile('int main(){ *(volatile int*)0 = 1; }')
assert binary is not None, diagnostic
report = sandbox.run(binary, '', 1000, 128)
assert report['status'] == 'RE', report['status']
assert report['exit_code'] == 0xC0000005, report['exit_code']
with connection() as db:
    try:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM submission_results ORDER BY id LIMIT 1')
            row = cur.fetchone()
            assert row, 'A seeded submission result is needed for this live regression'
            for code in (report['exit_code'], 0xFFFFFFFF, -11, 0, None):
                cur.execute('UPDATE submission_results SET exit_code=%s WHERE id=%s', (code, row['id']))
                cur.execute('SELECT exit_code FROM submission_results WHERE id=%s', (row['id'],))
                assert cur.fetchone()['exit_code'] == code
    finally:
        db.rollback()
print('PASS: sandbox access violation and five database exit-code round trips; transaction rolled back.')
