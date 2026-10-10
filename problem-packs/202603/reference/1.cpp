#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n;int answer=0;while(n--){unsigned x;cin>>x;int ones=__builtin_popcount(x),bits=32-__builtin_clz(x);if(2*ones==bits)++answer;}cout<<answer<<'\n';}
