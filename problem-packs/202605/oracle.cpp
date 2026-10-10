// Independent enumerator: tries every non-leaf initial center.
// Red visibility uses an explicit compressed ancestor forest, not the optimized
// reference's range-add tree or shared root-selection state.
#include <bits/stdc++.h>
#include <cassert>
using namespace std;
const int BIG=1000000007;
vector<vector<int>> adjacency;
vector<int> solve(int root){
 int n=adjacency.size();vector<int> parent(n,-1),order{root},key(n,BIG),nearest(n,-1),redParent(n,-1);vector<vector<int>> redChildren(n),byKey(n);vector<char> pending(n),open(n),red(n);
 for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:adjacency[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
 vector<int> initial=adjacency[root];initial.push_back(root);sort(initial.begin(),initial.end());deque<int> result(initial.begin(),initial.end());int head=result.front();
 set<pair<int,int>> boundary,visible;
 for(int u:order)if(u!=root){for(int v:adjacency[u])if(v!=parent[u]){key[u]=v;pending[u]=true;break;}if(pending[u]&&key[u]<head){red[u]=true;redParent[u]=nearest[parent[u]];byKey[key[u]].push_back(u);if(redParent[u]<0)visible.insert({key[u],u});else redChildren[redParent[u]].push_back(u);nearest[u]=u;}else nearest[u]=nearest[parent[u]];}
 for(int u:adjacency[root])if(pending[u]){open[u]=true;boundary.insert({key[u],u});}
 auto remove=[&](int u){if(!red[u])return;red[u]=false;int p=redParent[u];if(p<0)visible.erase({key[u],u});for(int v:redChildren[u])if(red[v]&&redParent[v]==u){redParent[v]=p;if(p<0)visible.insert({key[v],v});else redChildren[p].push_back(v);}};
 while(int(result.size())<n){int dangerous=visible.empty()?-1:visible.rbegin()->second,next=BIG;if(dangerous>=0){for(int v:adjacency[dangerous])if(v!=parent[dangerous]&&v>=head){next=v;break;}}
  auto it=boundary.upper_bound({head,BIG});int safe=it==boundary.end()?-1:it->second;int u=(safe>=0&&(dangerous<0||!open[dangerous]||(next<BIG&&key[safe]<next)))?safe:dangerous;assert(u>=0&&open[u]);boundary.erase({key[u],u});open[u]=false;remove(u);int before=head;
  vector<int> additions;for(int v:adjacency[u])if(v!=parent[u])additions.push_back(v);int split=lower_bound(additions.begin(),additions.end(),head)-additions.begin();for(int j=split-1;j>=0;--j)result.push_front(additions[j]);for(int j=split;j<int(additions.size());++j)result.push_back(additions[j]);pending[u]=false;
  for(int v:adjacency[u])if(v!=parent[u]&&pending[v]){open[v]=true;boundary.insert({key[v],v});}head=result.front();for(int v=head;v<before;++v)for(int r:byKey[v])remove(r);
 }
 return {result.begin(),result.end()};
}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n;adjacency.resize(n);for(int i=1;i<n;++i){int u,v;cin>>u>>v;adjacency[--u].push_back(--v);adjacency[v].push_back(u);}for(auto &row:adjacency)sort(row.begin(),row.end());vector<int> best(n,BIG);for(int u=0;u<n;++u)if(n==2||adjacency[u].size()>1)best=min(best,solve(u));for(int i=0;i<n;++i)cout<<best[i]+1<<(i+1==n?'\n':' ');}
