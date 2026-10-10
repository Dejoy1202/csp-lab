// Station boundary splitting and repaired-edge contraction are explained at
// https://pcs2.roj.ac.cn/problems/shumeng/CSP202603E/ .
// CSP Lab implementation: vector buckets and symmetric hash peer sets,
// independently checked by offline second-latest repair times and small BFS.
#include <bits/stdc++.h>
#include <cassert>
using namespace std;using Key=uint64_t;
Key pairKey(int a,int b){if(a>b)swap(a,b);return (Key(uint32_t(a))<<32)|uint32_t(b);}
struct TreeIndex {
 int n,levels;vector<vector<pair<int,int>>> graph;vector<int>depth,parent,edge;vector<vector<int>>up;
 TreeIndex(int count,const vector<pair<int,int>>&edges):n(count),levels(1),graph(n+1),depth(n+1),parent(n+1),edge(n+1){while((1<<levels)<=n)++levels;for(int i=0;i<(int)edges.size();++i){auto [a,b]=edges[i];graph[a].push_back({b,i});graph[b].push_back({a,i});}vector<int>order{1};parent[1]=1;for(size_t i=0;i<order.size();++i){int u=order[i];for(auto [v,id]:graph[u])if(v!=parent[u]){parent[v]=u;edge[v]=id;depth[v]=depth[u]+1;order.push_back(v);}}up.assign(levels,parent);for(int j=1;j<levels;++j)for(int v=1;v<=n;++v)up[j][v]=up[j-1][up[j-1][v]];}
 int jump(int u,int steps)const{for(int j=0;steps;++j,steps>>=1)if(steps&1)u=up[j][u];return u;}
 int lca(int u,int v)const{if(depth[u]<depth[v])swap(u,v);u=jump(u,depth[u]-depth[v]);if(u==v)return u;for(int j=levels-1;j>=0;--j)if(up[j][u]!=up[j][v]){u=up[j][u];v=up[j][v];}return parent[u];}
 int distance(int u,int v)const{return depth[u]+depth[v]-2*depth[lca(u,v)];}
 int toward(int from,int to)const{int w=lca(from,to);return w==from?jump(to,depth[to]-depth[from]-1):parent[from];}
 int edgeId(int u,int v)const{return parent[u]==v?edge[u]:edge[v];}
 vector<int> stops(int s,int t,const vector<int>&stations)const{int length=distance(s,t);vector<pair<int,int>>items{{0,s},{length,t}};for(int v:stations){if(v==s||v==t)continue;int first=distance(s,v);if(first+distance(v,t)==length)items.push_back({first,v});}sort(items.begin(),items.end());vector<int>result;for(auto item:items)result.push_back(item.second);return result;}
};

struct Travel {
 vector<int> parent,size,pending;vector<unordered_set<int>> neighbors,peers;
 unordered_map<Key,vector<int>> blocked;int answer=0;
 Travel(int count,int plans):parent(count),size(count,1),pending(plans),neighbors(count),peers(count){iota(parent.begin(),parent.end(),0);blocked.reserve(plans*2+1);}
 int root(int v){while(v!=parent[v]){parent[v]=parent[parent[v]];v=parent[v];}return v;}
 void add(int a,int b,int trip){Key key=pairKey(a,b);auto [it,inserted]=blocked.try_emplace(key);it->second.push_back(trip);if(inserted){peers[a].insert(b);peers[b].insert(a);}++pending[trip];}
 void release(int a,int b){auto it=blocked.find(pairKey(a,b));if(it==blocked.end())return;for(int trip:it->second)if(--pending[trip]==0)++answer;blocked.erase(it);peers[a].erase(b);peers[b].erase(a);}
 void repair(int u,int v){int a=root(u),b=root(v);if(a==b)return;if(size[a]<size[b])swap(a,b);
 neighbors[a].erase(b);neighbors[b].erase(a);
 // A,B were adjacent. Every old B-neighbor becomes adjacent to A.
 for(int next:neighbors[b]){neighbors[next].erase(b);neighbors[next].insert(a);neighbors[a].insert(next);release(a,next);}
 neighbors[b].clear();parent[b]=a;size[a]+=size[b];
 while(!peers[b].empty()){int other=*peers[b].begin();Key old=pairKey(b,other);auto it=blocked.find(old);assert(it!=blocked.end());auto trips=move(it->second);blocked.erase(it);peers[b].erase(other);peers[other].erase(b);
 if(other==a||neighbors[a].count(other)){for(int trip:trips)if(--pending[trip]==0)++answer;}
 else{Key key=pairKey(a,other);auto [target,created]=blocked.try_emplace(key);auto &destination=target->second;destination.insert(destination.end(),trips.begin(),trips.end());if(created){peers[a].insert(other);peers[other].insert(a);}}}
 }
};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,X;cin>>n>>X;vector<pair<int,int>>edges(n-1);for(auto &p:edges)cin>>p.first>>p.second;TreeIndex tree(n,edges);int k;cin>>k;vector<int>stations(k);vector<char>isStation(n+1);for(int &v:stations){cin>>v;isStation[v]=true;}
int nodes=n+1;vector<int>boundary(n-1,-1);vector<pair<int,int>>local(n-1,{-1,-1});for(int i=0;i<n-1;++i){auto [u,v]=edges[i];if(isStation[u]&&isStation[v])continue;if(isStation[u]||isStation[v]){boundary[i]=nodes++;local[i]={isStation[u]?v:u,boundary[i]};}else local[i]={u,v};}
int m;cin>>m;Travel travel(nodes,m);for(auto [u,v]:local)if(u>=0){travel.neighbors[u].insert(v);travel.neighbors[v].insert(u);}
for(int trip=0;trip<m;++trip){int s,t;cin>>s>>t;auto stops=tree.stops(s,t,stations);for(int j=1;j<(int)stops.size();++j){int u=stops[j-1],v=stops[j];if(tree.distance(u,v)<=1)continue;int a=isStation[u]?boundary[tree.edgeId(u,tree.toward(u,v))]:u;int b=isStation[v]?boundary[tree.edgeId(v,tree.toward(v,u))]:v;assert(a>=0&&b>=0);travel.add(a,b,trip);}if(travel.pending[trip]==0)++travel.answer;}
int q,last=0;cin>>q;while(q--){int type;cin>>type;if(type==2){last=travel.answer;cout<<last<<'\n';}else{int u,v;cin>>u>>v;u^=X*last;v^=X*last;int id=tree.edgeId(u,v);auto [a,b]=local[id];if(a>=0)travel.repair(a,b);}}
}
