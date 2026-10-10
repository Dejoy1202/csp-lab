"""Hash every business row before/after restarting CSP Lab; never print row data."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pymysql

ROOT=Path(__file__).resolve().parents[1]/'test-results/windows'

def snapshot():
    report={}
    with pymysql.connect(host=os.environ['DB_HOST'],port=int(os.environ['DB_PORT']),user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ['DB_NAME'],charset='utf8mb4') as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' AND TABLE_NAME<>'flyway_schema_history' ORDER BY TABLE_NAME",(os.environ['DB_NAME'],))
            names=[row[0] for row in cursor.fetchall()]
        for name in names:
            with db.cursor() as cursor:
                cursor.execute("SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND CONSTRAINT_NAME='PRIMARY' ORDER BY ORDINAL_POSITION",(os.environ['DB_NAME'],name))
                order=','.join('`'+row[0]+'`' for row in cursor.fetchall())
            assert order,'Each business table must have a deterministic primary key'
            digest=hashlib.sha256();count=0
            with db.cursor(pymysql.cursors.SSCursor) as cursor:
                cursor.execute(f'SELECT * FROM `{name}` ORDER BY {order}')
                for row in cursor:
                    digest.update(json.dumps(row,ensure_ascii=False,separators=(',',':'),default=str).encode('utf-8')+b'\n')
                    count+=1
            report[name]={'rows':count,'sha256':digest.hexdigest()}
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--after',action='store_true');args=parser.parse_args()
    ROOT.mkdir(parents=True,exist_ok=True)
    actual=snapshot()
    before=ROOT/'database-before.json'
    if not args.after:
        before.write_text(json.dumps(actual,indent=2),encoding='utf-8')
        print(f'Windows database snapshot: {len(actual)} business tables',flush=True)
    else:
        assert actual==json.loads(before.read_text(encoding='utf-8')),'Business rows changed during restart'
        (ROOT/'database-restart.json').write_text(json.dumps({'status':'PASS','checkedAt':datetime.datetime.now().isoformat(),'applicationStopStart':True,'mysqlServiceStopped':False,'tables':actual},indent=2),encoding='utf-8')
        print(f'PASS: all {len(actual)} tables and row hashes unchanged after application restart',flush=True)
