#include <bits/stdc++.h>
using namespace std;
int main(){int n,x;cin>>n;map<int,int> c;while(n--){cin>>x;c[x]++;}int best=-1,ans=0;for(auto [v,k]:c)if(k>best){best=k;ans=v;}cout<<ans<<'\n';}
