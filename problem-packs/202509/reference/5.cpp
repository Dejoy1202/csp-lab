// CSP Lab: convex balance DP compressed to slopes, with exact tie bookkeeping.
#include <bits/stdc++.h>
using namespace std;using ll=long long;using P=pair<ll,ll>;
P add(P a,P b){return {a.first+b.first,a.second+b.second};}P sub(P a,P b){return {a.first-b.first,a.second-b.second};}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;ll budget;cin>>n>>budget;vector<ll>a(n),b(n);ll full=0;for(ll &x:a){cin>>x;full+=x;}for(ll &x:b){cin>>x;full+=x;}if(full<=budget){cout<<n<<'\n';return 0;}
auto evaluate=[&](ll reward){priority_queue<P,vector<P>,greater<P>> heap;P zero{0,0};for(int i=0;i<n;++i){P up{a[i],0},down{b[i]-reward,-1},center=min(P{0,0},add(up,down)),lower=sub(center,down);zero=add(zero,center);if(!heap.empty()&&heap.top()<lower){zero=add(zero,sub(heap.top(),lower));heap.pop();heap.push(lower);}heap.push(sub(up,center));}ll count=-zero.second;return P{zero.first+reward*count,count};};
ll low=0,high=2000000001LL;while(low+1<high){ll mid=(low+high)/2;if(evaluate(mid).first<=budget)low=mid;else high=mid;}auto [cost,k]=evaluate(low);auto [nextCost,nextK]=evaluate(high);ll answer=k;if(nextK>k){ll marginal=(nextCost-cost)/(nextK-k);answer+=min(nextK-k,(budget-cost)/marginal);}cout<<answer<<'\n';}
