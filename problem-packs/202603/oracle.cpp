// Independent OFFLINE oracle: no DSU, component adjacency, or live pair buckets.
// Input operations are already decoded (X=0). Each road has its repair timestamp.
// A segment becomes feasible at its second-largest timestamp; a trip needs all segments.
#include <bits/stdc++.h>
#include <cassert>
using namespace std;
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

struct BestTwo {int first=0,second=0;};
BestTwo combine(BestTwo a,BestTwo b){array<int,4>values{a.first,a.second,b.first,b.second};sort(values.begin(),values.end(),greater<int>());return {values[0],values[1]};}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,X;cin>>n>>X;assert(X==0);vector<pair<int,int>>edges(n-1);for(auto &p:edges)cin>>p.first>>p.second;TreeIndex tree(n,edges);int k;cin>>k;vector<int>stations(k);for(int &v:stations)cin>>v;int m;cin>>m;vector<pair<int,int>>plans(m);for(auto &p:plans)cin>>p.first>>p.second;int q;cin>>q;vector<int>types(q),times(n-1,q+1);for(int i=0;i<q;++i){cin>>types[i];if(types[i]==1){int u,v;cin>>u>>v;int id=tree.edgeId(u,v);assert(times[id]==q+1);times[id]=i+1;}}
vector<vector<BestTwo>>best(tree.levels,vector<BestTwo>(n+1));for(int v=2;v<=n;++v)best[0][v]={times[tree.edge[v]],0};for(int j=1;j<tree.levels;++j)for(int v=1;v<=n;++v)best[j][v]=combine(best[j-1][v],best[j-1][tree.up[j-1][v]]);
auto collect=[&](int u,int steps){BestTwo result;for(int j=0;steps;++j,steps>>=1)if(steps&1){result=combine(result,best[j][u]);u=tree.up[j][u];}return result;};
vector<int>activation;activation.reserve(m);for(auto [s,t]:plans){auto stops=tree.stops(s,t,stations);int required=0;for(int j=1;j<(int)stops.size();++j){int u=stops[j-1],v=stops[j],w=tree.lca(u,v);auto top=combine(collect(u,tree.depth[u]-tree.depth[w]),collect(v,tree.depth[v]-tree.depth[w]));required=max(required,top.second);}activation.push_back(required);}sort(activation.begin(),activation.end());for(int i=0;i<q;++i)if(types[i]==2)cout<<upper_bound(activation.begin(),activation.end(),i+1)-activation.begin()<<'\n';
}
