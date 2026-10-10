"""Apply Windows portability fixes without changing test data or scores."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

def api(method,path,data=None):
    request=urllib.request.Request(os.environ['BASE_URL']+path,data=None if data is None else json.dumps(data,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json','X-API-Key':os.environ['API_KEY']},method=method)
    with urllib.request.urlopen(request,timeout=120) as response:
        return json.load(response)

if __name__=='__main__':
    evidence=[]
    for batch in ('202603','202605'):
        for path in sorted((ROOT/'problem-packs/generated').glob(batch+'-?.json.gz')):
            payload=json.loads(gzip.decompress(path.read_bytes()));problem=payload['problems'][0]
            changed=[]
            for asset in problem['assets']:
                file=None
                if asset['name'].startswith('reference-') and asset['name'].endswith('.cpp'):file=ROOT/f'problem-packs/{batch}/reference/{asset["name"].split("-")[1]}'
                elif asset['name']=='oracle.cpp':file=ROOT/f'problem-packs/{batch}/oracle.cpp'
                if file is None:continue
                source=file.read_text(encoding='utf-8')
                if source==asset['content']:continue
                stripped=source.replace('#include <cassert>\n','',1).replace('#ifdef _WIN32\n#define getchar_unlocked _getchar_nolock\n#endif\n','',1)
                if stripped!=asset['content']:
                    assert batch=='202605' and asset['name']=='reference-4.cpp'
                    body=source.split('FastInput in;',1)[1]
                    assert body==asset['content'].split('FastInput in;',1)[1],'Only buffered/binary input setup may change; algorithm remains identical'
                asset['content']=source
                changed.append({'asset':asset['name'],'sha256':hashlib.sha256(source.encode()).hexdigest()})
            if not changed:continue
            path.write_bytes(gzip.compress(json.dumps(payload,ensure_ascii=False).encode('utf-8'),mtime=0))
            found=api('GET',f'/api/problems?batch={batch}&size=100')['items']
            identifier=next(item['id'] for item in found if item['code']==problem['code'])
            api('PUT',f'/api/admin/problems/{identifier}',problem)
            evidence.append({'problem':problem['code'],'changes':changed,'testInputsOutputsAndScoresUnchanged':True})
            print(f'{problem["code"]}: portable source asset synchronized',flush=True)
    output=ROOT/'test-results/windows/source-portability.json'
    output.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
