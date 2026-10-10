#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n;vector<int> ordinary(n),even(n);for(int i=0;i<n;++i){string s;cin>>s;int a=stoi(s.substr(0,s.size()-2)),b=s.back()-'0';ordinary[i]=a+(b>=5);even[i]=a+(b>5||(b==5&&a%2));}for(auto row:{ordinary,even}){for(int i=0;i<n;++i)cout<<row[i]<<(i+1==n?'\n':' ');}}
