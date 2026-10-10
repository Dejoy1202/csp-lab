"""Twelve small original training problems with independent Python answer checks."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
from sandbox import Sandbox, tokens
from build import import_file

CPP_PREFIX="#include <bits/stdc++.h>\nusing namespace std;\nint main(){ios::sync_with_stdio(false);cin.tie(nullptr);\n"
PROBLEMS=[
    ("数组求和","基础", "输入一个非空整数数组，输出所有元素的和。", "第一行n；第二行n个整数。", "一个整数。", "1<=n<=1000；|a_i|<=10^9。", 'int n;cin>>n;long long ans=0,x;while(n--){cin>>x;ans+=x;}cout<<ans<<"\\n";'),
    ("排序去重","排序", "把整数数组去重后从小到大输出。", "第一行n；第二行n个整数。", "第一行不同整数个数；第二行升序排列的不同整数。", "1<=n<=1000；|a_i|<=10000。", 'int n,x;cin>>n;set<int>s;while(n--){cin>>x;s.insert(x);}cout<<s.size()<<"\\n";for(int v:s)cout<<v<<" ";cout<<"\\n";'),
    ("区间账单","前缀和", "对给定数组回答闭区间[l,r]的元素和，编号从1开始。", "第一行n q；第二行n个整数；后续q行l r。", "每次查询一行整数。", "1<=n,q<=1000；|a_i|<=10^9；1<=l<=r<=n。", 'int n,q;cin>>n>>q;vector<long long>p(n+1);for(int i=1;i<=n;i++){cin>>p[i];p[i]+=p[i-1];}while(q--){int l,r;cin>>l>>r;cout<<p[r]-p[l-1]<<"\\n";}'),
    ("批量加班补贴","差分", "n个位置初值为0，每次把闭区间[l,r]都增加v。输出所有修改后的数组。", "第一行n q；后续q行l r v。", "一行n个最终整数。", "1<=n,q<=1000；|v|<=10^9；1<=l<=r<=n。", 'int n,q;cin>>n>>q;vector<long long>d(n+2);while(q--){int l,r;long long v;cin>>l>>r>>v;d[l]+=v;d[r+1]-=v;}long long s=0;for(int i=1;i<=n;i++){s+=d[i];cout<<s<<" ";}cout<<"\\n";'),
    ("两个周期","数学", "输入两个正整数，输出最大公约数和最小公倍数。", "一行a b。", "一行两个整数，先最大公约数，后最小公倍数。", "1<=a,b<=10^9。", 'long long a,b;cin>>a>>b;auto g=gcd(a,b);cout<<g<<" "<<a/g*b<<"\\n";'),
    ("最佳连续收益","动态规划", "选择一个非空连续子数组，使元素和最大。", "第一行n；第二行n个整数。", "一行最大和。", "1<=n<=1000；|a_i|<=10^9；不允许空数组。", 'int n;cin>>n;long long x,cur=0,best=LLONG_MIN;for(int i=0;i<n;i++){cin>>x;cur=(i?max(x,cur+x):x);best=max(best,cur);}cout<<best<<"\\n";'),
    ("括号核对","栈", "判断只由()[]{}组成的字符串是否正确匹配。每个闭括号必须匹配最近尚未闭合的同类开括号。", "一行非空字符串。", "匹配输出YES，否则NO。", "长度1..2000。", ""),
    ("最少换乘边数","BFS", "无向图中求1号节点到每个节点的最短边数，不可达为-1。", "第一行n m；后续m行边u v。", "一行n个距离，按节点编号输出。", "1<=n<=1000；0<=m<=5000；允许重边与自环。", 'int n,m;cin>>n>>m;vector<vector<int>>g(n+1);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);g[v].push_back(u);}vector<int>d(n+1,-1);queue<int>q;q.push(1);d[1]=0;while(!q.empty()){int u=q.front();q.pop();for(int v:g[u])if(d[v]<0){d[v]=d[u]+1;q.push(v);}}for(int i=1;i<=n;i++)cout<<d[i]<<" ";cout<<"\\n";'),
    ("社团联通查询","并查集", "初始n个成员各属不同组。操作1 a b合并两组；操作2 a b查询是否在同组。", "第一行n q；后续q行op a b。", "对每个操作2输出YES或NO。", "1<=n,q<=1000；1<=a,b<=n；op为1或2。", 'int n,q;cin>>n>>q;vector<int>p(n+1);iota(p.begin(),p.end(),0);function<int(int)>f=[&](int x){return p[x]==x?x:p[x]=f(p[x]);};while(q--){int op,a,b;cin>>op>>a>>b;a=f(a);b=f(b);if(op==1)p[a]=b;else cout<<(a==b?"YES":"NO")<<"\\n";}'),
    ("重叠预约合并","贪心", "把有公共点的闭区间反复合并，输出最后的区间数量。相邻但没有公共点的区间不合并。", "第一行n；之后n行l r。", "一行最终区间数量。", "1<=n<=1000；-10^9<=l<=r<=10^9。", 'int n;cin>>n;vector<pair<long long,long long>>a(n);for(auto&v:a)cin>>v.first>>v.second;sort(a.begin(),a.end());int k=0;long long end=LLONG_MIN;for(auto [l,r]:a){if(k==0||l>end){k++;end=r;}else end=max(end,r);}cout<<k<<"\\n";'),
    ("严格上升选取","二分", "从数组中按原顺序选取元素，求严格递增子序列的最大长度。", "第一行n；第二行n个整数。", "一行最大长度。", "1<=n<=1000；|a_i|<=10^9；相同元素不能连续选入严格递增序列。", 'int n;cin>>n;vector<long long>t;while(n--){long long x;cin>>x;auto p=lower_bound(t.begin(),t.end(),x);if(p==t.end())t.push_back(x);else *p=x;}cout<<t.size()<<"\\n";'),
    ("有限背包","背包", "每件物品至多取一次，在总重量不超过W时最大化价值；允许一件都不取。", "第一行n W；后续n行重量w与价值v。", "一行最大总价值。", "1<=n<=100；0<=W<=1000；1<=w<=100；0<=v<=10^6。", 'int n,W;cin>>n>>W;vector<int>d(W+1);while(n--){int w,v;cin>>w>>v;for(int j=W;j>=w;j--)d[j]=max(d[j],d[j-w]+v);}cout<<d[W]<<"\\n";'),
]
# Keep the bracket source readable rather than nesting escaped literals.
PROBLEMS[6]=(*PROBLEMS[6][:-1],r'''string s,t;cin>>s;bool ok=true;for(char c:s){if(c=='('||c=='['||c=='{')t+=c;else{char need=c==')'?'(':c==']'?'[':'{';if(t.empty()||t.back()!=need){ok=false;break;}t.pop_back();}}cout<<(ok&&t.empty()?"YES":"NO")<<"\n";''')

def cases(position,rng):
    generated=[]
    for i in range(8):
        n=[1,2,8,30,100,1000,1000,1000][i]
        a=[rng.randint(-10**9,10**9) for _ in range(n)]
        if i==0:a=[-10**9]
        if i==1:a=[10**9,10**9]
        if position in (1,2,6,11):
            if position==2:a=[rng.randint(-10000,10000) for _ in range(n)]
            if position==6 and i==6:a=[-rng.randint(1,100) for _ in range(n)]
            if position==11 and i==6:a=[7]*n
            data=str(n)+"\n"+" ".join(map(str,a))+"\n"
            if position==1:answer=str(sum(a))+"\n"
            elif position==2:
                unique=sorted(set(a));answer=str(len(unique))+"\n"+" ".join(map(str,unique))+"\n"
            elif position==6:
                # Prefix minima; independent of the C++ Kadane recurrence.
                running=smallest=0;best=-10**30
                for x in a:running+=x;best=max(best,running-smallest);smallest=min(smallest,running)
                answer=str(best)+"\n"
            else:
                dp=[1]*n
                for j in range(n):dp[j]=1+max((dp[k] for k in range(j) if a[k]<a[j]),default=0)
                answer=str(max(dp))+"\n"
        elif position in (3,4):
            q=100 if i<5 else 1000;ops=[];ans=[];values=[0]*n
            for _ in range(q):
                l=rng.randrange(n);r=rng.randrange(l,n)
                if position==3:ops.append(f"{l+1} {r+1}");ans.append(str(sum(a[l:r+1])))
                else:
                    v=rng.randint(-10**9,10**9);ops.append(f"{l+1} {r+1} {v}")
                    for j in range(l,r+1):values[j]+=v
            data=f"{n} {q}\n"+(" ".join(map(str,a))+"\n" if position==3 else "")+"\n".join(ops)+"\n"
            answer="\n".join(ans)+"\n" if position==3 else " ".join(map(str,values))+"\n"
        elif position==5:
            import math
            x,y=([(1,1),(10**9,999999999),(24,36),(1,10**9)][i] if i<4 else (rng.randint(1,10**9),rng.randint(1,10**9)))
            g=math.gcd(x,y);data=f"{x} {y}\n";answer=f"{g} {x*y//g}\n"
        elif position==7:
            examples=["(",")","([]{})","([)]","(((())))","[]"*1000,"{"*1000+"}"*1000,"{"*1000+"}"*999+"]"]
            data=examples[i]+"\n";s=data.strip()
            while any(pair in s for pair in ("()","[]","{}")):
                for pair in ("()","[]","{}"):s=s.replace(pair,"")
            answer="YES\n" if not s else "NO\n"
        elif position==8:
            m=0 if i==0 else (5000 if i==7 else min(5000,n*3));edges=[(rng.randint(1,n),rng.randint(1,n)) for _ in range(m)]
            g=[set() for _ in range(n)]
            for u,v in edges:g[u-1].add(v-1);g[v-1].add(u-1)
            distance=[-1]*n;distance[0]=0;frontier={0};depth=0
            while frontier:
                nxt=set().union(*(g[v] for v in frontier));depth+=1
                frontier={v for v in nxt if distance[v]<0}
                for v in frontier:distance[v]=depth
            data=f"{n} {m}\n"+"".join(f"{u} {v}\n" for u,v in edges);answer=" ".join(map(str,distance))+"\n"
        elif position==9:
            q=1000;labels=list(range(n));ops=[];answers=[]
            for j in range(q):
                op=1 if j%3==0 else 2;x=rng.randrange(n);y=rng.randrange(n);ops.append(f"{op} {x+1} {y+1}")
                if op==1:
                    old,new=labels[x],labels[y];labels=[new if v==old else v for v in labels]
                else:answers.append("YES" if labels[x]==labels[y] else "NO")
            data=f"{n} {q}\n"+"\n".join(ops)+"\n";answer="\n".join(answers)+"\n"
        elif position==10:
            intervals=[]
            for j in range(n):
                l=rng.randint(-10**9,10**9);r=l+rng.randint(0,10000000);r=min(r,10**9);intervals.append((l,r))
            if i==6:intervals=[(j,j+1) for j in range(n)]
            if i==7:intervals=[(2*j,2*j) for j in range(n)]
            events=[(l,0) for l,r in intervals]+[(r,1) for l,r in intervals];events.sort();active=count=0
            for x,kind in events:
                if kind==0:
                    if active==0:count+=1
                    active+=1
                else:active-=1
            data=str(n)+"\n"+"".join(f"{l} {r}\n" for l,r in intervals);answer=str(count)+"\n"
        else:
            n=min(n,100);W=0 if i==0 else (1000 if i==7 else rng.randint(1,1000));items=[(rng.randint(1,100),rng.randint(0,10**6)) for _ in range(n)]
            states={0:0}
            for w,v in items:
                nxt=dict(states)
                for old,value in states.items():
                    if old+w<=W:nxt[old+w]=max(nxt.get(old+w,0),value+v)
                states=nxt
            data=f"{n} {W}\n"+"".join(f"{w} {v}\n" for w,v in items);answer=str(max(states.values()))+"\n"
        generated.append((data,answer))
    return generated

def build_originals(output,import_now):
    output.mkdir(parents=True,exist_ok=True);sandbox=Sandbox(os.environ.get("SANDBOX_IMAGE","csp-lab-sandbox:local"),"original-pack-build")
    for position,(title,tag,statement,inp,out,limits,body) in enumerate(PROBLEMS,1):
        source=CPP_PREFIX+body+"\n}\n";binary,diagnostic=sandbox.compile(source);assert binary,diagnostic
        pairs=cases(position,random.Random(1000+position));tests=[];checks=[]
        for i,(data,answer) in enumerate(pairs):
            result=sandbox.run(binary,data,1000,128,1024)
            assert result["status"]=="OK" and tokens(result["stdout"].encode())==tokens(answer.encode()),f"Original {position} case {i} failed"
            tests.append({"input":data,"output":answer,"score":15 if i<4 else 10,"subtaskKey":None})
            checks.append({"inputSha256":hashlib.sha256(data.encode()).hexdigest(),"outputSha256":hashlib.sha256(answer.encode()).hexdigest()})
        report=json.dumps({"status":"VERIFIED","original":True,"independentPythonOracle":True,"testCount":8,"checksums":checks},ensure_ascii=False)
        p={"code":f"LAB-{position:03d}","title":title,"sourceYear":None,"sourceBatch":"ORIGINAL","sourcePosition":None,"difficulty":"EASY" if position<8 else "MEDIUM","tags":[tag],"timeLimitMs":1000,"memoryLimitMb":128,"sourceUrl":None,
           "statement":statement+" 本题为 CSP Lab 原创训练任务。","inputDescription":inp,"outputDescription":out,"constraintsDescription":limits,"scoringNotes":"本站原创评分：前4点各15分，后4点各10分；逐点计分，共100分。",
           "evaluationType":"FULL","constructionStatus":"VERIFIED","license":"CSP Lab original task and generated test data","samples":[{"input":pairs[0][0],"output":pairs[0][1]}],"testCases":tests,"subtasks":[],"outputLimitKb":1024,"validationReport":report,
           "assets":[{"name":"reference.cpp","kind":"REFERENCE","content":source},{"name":"originals.py","kind":"GENERATOR","content":Path(__file__).read_text(encoding="utf-8")} ]}
        path=output/f"LAB-{position:03d}.json.gz";path.write_bytes(gzip.compress(json.dumps({"problems":[p]},ensure_ascii=False).encode(),mtime=0))
        if import_now:print(import_file(path),flush=True)
        print(f"LAB-{position:03d}: 8 independent checks passed",flush=True)

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--import",dest="import_now",action="store_true");args=parser.parse_args()
    build_originals(Path("/output"),args.import_now)
