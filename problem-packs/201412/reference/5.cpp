// Cyclic seven-day min-cost transshipment; Dijkstra and reduced-cost potentials.
#include <bits/stdc++.h>
using namespace std;
struct Arc{int to,rev,cap,cost;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;int S=7*n,T=S+1,V=T+1;vector<vector<Arc>>g(V);auto add=[&](int a,int b,int cap,int cost){g[a].push_back({b,(int)g[b].size(),cap,cost});g[b].push_back({a,(int)g[a].size()-1,0,-cost});};int required=0;auto node=[](int city,int day){return city*7+day;};
for(int i=0;i<n;++i){int a[7],b[7],v,w;for(int&x:a)cin>>x;for(int&x:b)cin>>x;cin>>v>>w;for(int d=0;d<7;++d){int balance=a[d]-b[d];if(balance>0){add(S,node(i,d),balance,0);required+=balance;}if(balance<0)add(node(i,d),T,-balance,0);add(node(i,d),node(i,(d+1)%7),v,w);}}
for(int i=0;i<m;++i){int a,b,c;cin>>a>>b>>c;--a;--b;for(int d=0;d<7;++d){add(node(a,d),node(b,d),1000000,c);add(node(b,d),node(a,d),1000000,c);}}
const long long INF=1LL<<60;vector<long long>potential(V),dist(V);vector<int>from(V),index(V);int flow=0;long long answer=0;
while(flow<required){fill(dist.begin(),dist.end(),INF);dist[S]=0;priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;q.push({0,S});while(!q.empty()){auto [d,u]=q.top();q.pop();if(d!=dist[u])continue;for(int i=0;i<(int)g[u].size();++i){auto e=g[u][i];long long nd=d+e.cost+potential[u]-potential[e.to];if(e.cap&&nd<dist[e.to]){dist[e.to]=nd;from[e.to]=u;index[e.to]=i;q.push({nd,e.to});}}}if(dist[T]==INF){cerr<<"Infeasible input";return 2;}for(int i=0;i<V;++i)if(dist[i]!=INF)potential[i]+=dist[i];int pushed=required-flow;for(int v=T;v!=S;v=from[v])pushed=min(pushed,g[from[v]][index[v]].cap);long long cost=0;for(int v=T;v!=S;v=from[v]){auto&e=g[from[v]][index[v]];cost+=e.cost;e.cap-=pushed;g[v][e.rev].cap+=pushed;}flow+=pushed;answer+=cost*pushed;}
cout<<answer<<'\n';}
