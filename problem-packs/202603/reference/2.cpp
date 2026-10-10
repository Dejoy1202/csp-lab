#include <bits/stdc++.h>
using namespace std;
struct Task{int cost,gain;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;long long total=0;vector<Task> regular,flexible;for(int i=0;i<n;++i){int type,t,a,b;cin>>type>>t>>a>>b;total+=t;(type==1?regular:flexible).push_back({a,b});}
vector<long long> dp(m+1,-1000000000);dp[0]=0;for(auto task:regular)for(int j=m;j>=task.cost;--j)dp[j]=max(dp[j],dp[j-task.cost]+task.gain);
sort(flexible.begin(),flexible.end(),[](Task a,Task b){return 1LL*a.gain*b.cost>1LL*b.gain*a.cost;});vector<long double> savings(m+1);for(int budget=0;budget<=m;++budget){int remaining=budget;long double value=0;for(auto task:flexible){int used=min(remaining,task.cost);value+=(long double)used*task.gain/task.cost;remaining-=used;if(!remaining)break;}savings[budget]=value;}
long double best=0;for(int used=0;used<=m;++used)if(dp[used]>=0)best=max(best,dp[used]+savings[m-used]);cout<<fixed<<setprecision(15)<<(total-best)<<'\n';}
