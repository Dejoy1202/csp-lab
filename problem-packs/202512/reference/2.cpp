#include <bits/stdc++.h>
using namespace std;
int f(int x,int k){return ((x*x+k*k)%8)^k;}
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);
 int n,m;cin>>n>>m;vector<int>k(m);for(int&x:k)cin>>x;
 array<int,512>inverse{};
 for(int start=0;start<512;start++){
  int x=start;
  for(int key:k){int a=x>>6,b=x>>3&7,c=x&7;x=(b<<6)|((c^f(b,key))<<3)|(a^f(c,key));}
  inverse[x]=start;
 }
 for(int i=0;i<n;i++){int x;cin>>x;if(i)cout<<' ';cout<<inverse[x];}cout<<'\n';
}
