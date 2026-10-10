"""Additional exhaustive checks, separately from the formal sample/test points."""
import itertools,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import data
from sandbox import Sandbox
from validation_runtime import ValidationRuntime
ROOT=Path(__file__).resolve().parent

def batch_check(source,inputs,answers,time_ms=120000):
    sb=Sandbox('csp-lab-sandbox:local','probe39')
    binary,error=sb.compile(source);assert binary is not None,error
    with ValidationRuntime(sb,binary,time_ms,512,4096) as runtime:
        result=runtime.run(str(len(inputs))+'\n'+''.join(inputs));assert result['status']=='OK',result
    assert result['stdout'].split()==('\n'.join(answers)).split()
    return dict(timeMs=result['time_ms'],memoryKb=result['memory_kb'])

def main():
    ref=(ROOT/'reference/5.cpp').read_text(encoding='utf-8').replace('int main(){','int solve(){',1).replace("cout<<answer<<'\\n';}","cout<<answer<<'\\n';return 0;}")
    ref+='\nint main(){ios::sync_with_stdio(false);cin.tie(nullptr);int T;cin>>T;while(T--)solve();}\n'
    inputs=[];answers=[]
    for n,domain in [(1,range(1,4)),(2,range(1,4)),(3,range(1,4)),(4,range(1,3))]:
        for values in itertools.product(domain,repeat=2*n):
            a,b=list(values[:n]),list(values[n:]);full=sum(a)+sum(b)
            for budget in sorted({1,full//2,max(1,full//2-1),full//2+1,full-1,full,full+1}):
                text=data.encode_e(budget,a,b);inputs.append(text);answers.append(str(data.schedule_dp(budget,a,b)))
    r=random.Random(data.SEED+999)
    for i in range(100):
        text=data.make_e(r,1+i%20);m,a,b=data.parse(5,text);inputs.append(text);answers.append(str(data.schedule_dp(m,a,b)))
    e_result=batch_check(ref,inputs,answers)
    # Huffman strings for all padding residues, zero padding, and H escaping.
    samples=[];expected=[]
    for chars in ('ab','0HabcD1xy'):
        desc=data.make_huffman(chars,skew=len(chars)==9);codes=data.tree_codes(desc);ops=[];lines=[];padding=set()
        for length in range(1,151):
            word=''.join(chars[(j+length)%len(chars)] for j in range(length));encoded=data.encode_field(word,codes,True)
            if len(encoded)>150:continue
            padding.add(int(encoded[-2:],16));ops.append('3 0 '+encoded+' '+data.encode_field(word,codes,False));lines.append(f'{word}: {word}')
        ops+=['3 0 '+'H'*150+' '+'X'*150,'2 0 HHFirst HHValue','2 2 HHNext','1 2']
        lines+=['H'*149+': '+'X'*150,'HFirst: HValue','HFirst: HNext','HFirst: HNext']
        text='1 1\nRaw HStatic\n'+desc+'\n'+str(len(ops))+'\n'+'\n'.join(ops)+'\n';data.validate(3,text)
        oracle,_=data.headers(data.parse(3,text));assert oracle=='\n'.join(lines)+'\n'
        samples.append(text);expected.append(oracle);assert padding==set(range(8))
    ref3=(ROOT/'reference/3.cpp').read_text(encoding='utf-8').replace('int main(){','int solve(){',1).replace('cin>>description;build();','cin>>description;tree.clear();cursor=0;build();').replace('count=min(D,count+1);}}}','count=min(D,count+1);}}return 0;}')
    ref3+='\nint main(){ios::sync_with_stdio(false);cin.tie(nullptr);int T;cin>>T;while(T--)solve();}\n'
    c_result=batch_check(ref3,samples,expected)
    report=dict(batch='202509',status='PASS',scheduleExhaustiveAndRandomCases=len(inputs),huffmanCompletePaddingTraces=len(samples),paddingResidues=list(range(8)),schedule=e_result,huffman=c_result)
    Path('/output/202509-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
