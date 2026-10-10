#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
using namespace std;
int main(){int n,m;string q;cin>>n>>m>>q;long long Q=stoll(q.substr(0,1))*1000+stoll(q.substr(2));vector<int>value(n),weight(n);int sum=0;for(int &v:value){cin>>v;sum+=v;}for(int &w:weight){string s;cin>>s;int t=stoi(s.substr(0,1))*10+stoi(s.substr(2));w=t*t;}const int INF=1000000000;vector<int>dp(sum+1,INF);dp[0]=0;for(int i=0;i<n;++i)for(int v=sum;v>=value[i];--v)if(dp[v-value[i]]<INF)dp[v]=min(dp[v],dp[v-value[i]]+weight[i]);long long limit=10000LL*m;for(int v=sum;v>=0;--v)if(dp[v]<INF&&1LL*dp[v]*Q*Q<=limit*limit){cout<<v<<'\n';break;}}
