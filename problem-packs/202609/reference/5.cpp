#include <iostream>
#include <vector>
#include <array>
#include <algorithm>
#include <cstdint>
using namespace std;
struct Counter {
    vector<uint64_t> keys;vector<int> count;int mask=0,k=1;
    static uint64_t hash(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
    Counter(vector<uint64_t> values,int mod):k(mod){sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());int size=1;while(size<(int)values.size()*2)size*=2;mask=size-1;keys.assign(size,UINT64_MAX);count.assign(size*k,0);for(auto v:values){int at=hash(v)&mask;while(keys[at]!=UINT64_MAX)at=(at+1)&mask;keys[at]=v;}}
    int find(uint64_t key)const{int at=hash(key)&mask;while(keys[at]!=UINT64_MAX){if(keys[at]==key)return at;at=(at+1)&mask;}return -1;}
    int get(uint64_t key,int residue)const{int at=find(key);return at<0?0:count[at*k+residue];}
};
struct Record{uint64_t parity;int all,branch,posAll,posBranch,residue,center;};
struct Visit{uint64_t parity;int vertex,parent,residue;};
int n,m,k,q;vector<vector<pair<int,int>>>graph;vector<int>color,parentNode,subtree;vector<char>removed,active;vector<vector<Record>>paths;vector<Counter>tables;
void build(int start){
    vector<int>order{start};parentNode[start]=-1;
    for(size_t i=0;i<order.size();++i){int u=order[i];for(auto [v,w]:graph[u])if(!removed[v]&&v!=parentNode[u]){parentNode[v]=u;order.push_back(v);}}
    for(int i=(int)order.size()-1;i>=0;--i){int u=order[i];subtree[u]=1;for(auto [v,w]:graph[u])if(!removed[v]&&parentNode[v]==u)subtree[u]+=subtree[v];}
    int center=-1,total=order.size();
    for(int u:order){int largest=total-subtree[u];for(auto [v,w]:graph[u])if(!removed[v]&&parentNode[v]==u)largest=max(largest,subtree[v]);if(largest*2<=total){center=u;break;}}
    removed[center]=1;int all=tables.size();tables.emplace_back(vector<uint64_t>{},k);
    uint64_t bit=1ULL<<color[center];vector<uint64_t>allKeys{bit};vector<pair<int,int>>entries;
    paths[center].push_back({bit,all,-1,-1,-1,0,center});entries.push_back({center,(int)paths[center].size()-1});
    vector<int>children;
    for(auto [neighbor,weight]:graph[center])if(!removed[neighbor]){
        children.push_back(neighbor);int branch=tables.size();vector<uint64_t>keys;vector<pair<int,int>>own;
        vector<Visit>todo{{bit^(1ULL<<color[neighbor]),neighbor,center,weight%k}};
        while(!todo.empty()){auto current=todo.back();todo.pop_back();int u=current.vertex;keys.push_back(current.parity);allKeys.push_back(current.parity);
            paths[u].push_back({current.parity,all,branch,-1,-1,current.residue,center});auto entry=make_pair(u,(int)paths[u].size()-1);entries.push_back(entry);own.push_back(entry);
            for(auto [v,w]:graph[u])if(!removed[v]&&v!=current.parent)todo.push_back({current.parity^(1ULL<<color[v]),v,u,(current.residue+w)%k});
        }
        tables.emplace_back(move(keys),k);for(auto [u,index]:own)paths[u][index].posBranch=tables[branch].find(paths[u][index].parity);
    }
    tables[all]=Counter(move(allKeys),k);for(auto [u,index]:entries)paths[u][index].posAll=tables[all].find(paths[u][index].parity);
    for(int child:children)build(child);
}
long long neighbors(int vertex){long long result=0;for(const auto&r:paths[vertex]){int residue=(k-r.residue)%k;uint64_t base=r.parity^(1ULL<<color[r.center]);for(int c=0;c<m;++c){uint64_t key=base^(1ULL<<c);result+=tables[r.all].get(key,residue);if(r.branch>=0)result-=tables[r.branch].get(key,residue);}}return result;}
void change(int vertex,int delta){for(const auto&r:paths[vertex]){tables[r.all].count[r.posAll*k+r.residue]+=delta;if(r.branch>=0)tables[r.branch].count[r.posBranch*k+r.residue]+=delta;}}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);cin>>n>>m>>k>>q;string initial;cin>>initial;color.resize(n);for(int&c:color){cin>>c;--c;}graph.resize(n);for(int i=1;i<n;++i){int u,v,w;cin>>u>>v>>w;--u;--v;graph[u].push_back({v,w});graph[v].push_back({u,w});}parentNode.resize(n);subtree.resize(n);removed.assign(n,0);active.assign(n,0);paths.resize(n);tables.reserve(2*n);build(0);long long answer=0;
auto toggle=[&](int u){if(active[u]){answer-=neighbors(u);change(u,-1);active[u]=0;}else{answer+=neighbors(u)+1;change(u,1);active[u]=1;}};
for(int i=0;i<n;++i)if(initial[i]=='1')toggle(i);cout<<answer<<'\n';while(q--){int u;cin>>u;toggle(u-1);cout<<answer<<'\n';}}
