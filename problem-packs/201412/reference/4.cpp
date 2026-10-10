// Kruskal with union by size and path compression.
#include <bits/stdc++.h>
using namespace std;
struct Edge{int a,b,w;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;vector<Edge>e(m);for(auto&x:e)cin>>x.a>>x.b>>x.w;sort(e.begin(),e.end(),[](Edge a,Edge b){return a.w<b.w;});vector<int>parent(n+1),size(n+1,1);iota(parent.begin(),parent.end(),0);auto root=[&](int x){while(parent[x]!=x){parent[x]=parent[parent[x]];x=parent[x];}return x;};long long total=0;int used=0;for(auto x:e){int a=root(x.a),b=root(x.b);if(a==b)continue;if(size[a]<size[b])swap(a,b);parent[b]=a;size[a]+=size[b];total+=x.w;if(++used==n-1)break;}cout<<total<<'\n';}
