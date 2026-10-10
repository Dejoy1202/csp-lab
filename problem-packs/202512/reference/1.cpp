#include <bits/stdc++.h>
using namespace std;
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);
 int n,m;cin>>n>>m;vector<int>a(n+1);for(int i=1;i<=n;i++)cin>>a[i];
 vector<vector<int>>s(m),t(m);vector<int>hs(m),ht(m);
 for(int side=0;side<2;side++)for(int i=0;i<m;i++){
  int len;cin>>len;auto&v=side?t[i]:s[i];int&h=side?ht[i]:hs[i];
  v.resize(len);for(int&x:v){cin>>x;h^=a[x];}
 }
 for(int i=0;i<m;i++)cout<<(((s[i]==t[i])==(hs[i]==ht[i]))?"correct":"wrong")<<'\n';
}
