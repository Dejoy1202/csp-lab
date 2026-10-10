// Independently authored CSP Lab C++17 reference.
#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n;vector<int>count(n+1);for(int i=0;i<n;++i){int x;cin>>x;if(i)cout<<' ';cout<<++count[x];}cout<<'\n';}
