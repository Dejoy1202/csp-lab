#include <bits/stdc++.h>
using namespace std;
int main(){int n;cin>>n;vector<long long> h(n+1);for(int i=0;i<n;i++)cin>>h[i];vector<int>s;long long ans=0;for(int i=0;i<=n;i++){while(!s.empty()&&h[s.back()]>h[i]){auto v=h[s.back()];s.pop_back();int l=s.empty()?0:s.back()+1;ans=max(ans,v*(i-l));}s.push_back(i);}cout<<ans<<'\n';}
