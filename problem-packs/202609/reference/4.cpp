#include <iostream>
#include <vector>
#include <algorithm>
#include <set>
#include <queue>
using namespace std;
using I=__int128_t;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,op;long long k;cin>>n>>k>>op;vector<long long>a(n);for(auto &x:a)cin>>x;sort(a.begin(),a.end());vector<int>color(n,-1);vector<int>remaining(n+1);for(int i=0;i<=n;++i)remaining[i]=i;auto successor=[&](int x){while(remaining[x]!=x){remaining[x]=remaining[remaining[x]];x=remaining[x];}return x;};queue<int>todo;bool edge=false;
auto index=[&](I value){if(value>1000000000000000000LL)return n;return (int)(lower_bound(a.begin(),a.end(),(long long)value)-a.begin());};
while(successor(0)<n){int start=successor(0);remaining[start]=successor(start+1);color[start]=0;todo.push(start);while(!todo.empty()){int u=todo.front();todo.pop();auto visit=[&](I low,I high){int begin=index(low),end=index(high);int v=successor(begin);while(v<end){remaining[v]=successor(v+1);color[v]=color[u]^1;todo.push(v);edge=true;v=successor(v);}};if(!op){visit((I)a[u]*k,(I)a[u]*k+1);if(a[u]%k==0)visit(a[u]/k,(I)a[u]/k+1);}else{visit((I)a[u]*k,(I)a[u]*(k+1));visit(a[u]/(k+1)+1,(I)(a[u]/k)+1);}}}
int count=edge?2:1;vector<vector<long long>>groups(3);for(int i=0;i<n;++i)groups[color[i]].push_back(a[i]);bool valid=true;
for(auto &group:groups)for(long long x:group){auto it=lower_bound(group.begin(),group.end(),(I)x*k,[](long long a,I b){return (I)a<b;});if(it!=group.end()&&(!op?(I)*it==(I)x*k:(I)*it<(I)x*(k+1)))valid=false;}
if(!valid){count=3;for(auto &g:groups)g.clear();for(long long x:a){int level=0;for(long long v=x;v>=k;v/=k)++level;groups[level%3].push_back(x);}}
cout<<count<<'\n';for(int i=0;i<count;++i){cout<<groups[i].size();for(long long x:groups[i])cout<<' '<<x;cout<<'\n';}}
