#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;const long long mod=1000000007;array<long long,16>d{},e{};d[0]=1;for(int i=0;i<n;i++){e.fill(0);for(int s=0;s<16;s++)for(int c=0;c<4;c++){if(i==0&&c==0)continue;if(c==0&&(s&2))continue;if(c==1&&!(s&1))continue;if(c==2&&(s&8))continue;if(c==3&&!(s&4))continue;int t=s|(1<<c);e[t]=(e[t]+d[s])%mod;}d=e;}cout<<d[15]<<'\n';}
