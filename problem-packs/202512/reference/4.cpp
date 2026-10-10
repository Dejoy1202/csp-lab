#include <bits/stdc++.h>
using namespace std;
constexpr int P=998244353;
using V=array<int,6>;
V local(int p,int e){
 vector<int>pw(3*e+1,1);for(int i=1;i<=3*e;i++)pw[i]=1LL*pw[i-1]*p%P;
 V v{};auto add=[&](int t,int x){v[t]=(v[t]+1LL*x)%P;};
 for(int x=-e;x<=e;x++)for(int y=-e;y<=e;y++)if(x+y<=e)add(0,pw[e-x-y]);
 for(int y=-e;y<=e;y++)add(1,pw[e-y]);
 for(int x=-e;x<=e;x++){
  if(2*x<=e)add(2,pw[e-2*x]);add(3,pw[e]);
  if(-2*x>=-e&&-2*x<=e)add(4,pw[e+x]);
 }
 v[5]=pw[e];return v;
}
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);
 int op,n;cin>>op>>n;
 vector<int>sp(n+1),core(n+1),primes;vector<unsigned char>ex(n+1);
 vector<V>value(n+1);value[1].fill(1);V sum=value[1];
 unordered_map<long long,V>higher;
 for(int b=2;b<=n;b++){
  if(!sp[b]){sp[b]=b;core[b]=1;ex[b]=1;primes.push_back(b);}
  int p=sp[b],e=ex[b];V v;
  if(e==1){
   int p2=1LL*p*p%P,p3=1LL*p2*p%P;
   v={(int)((p3+2LL*p2+3LL*p+2)%P),(int)((p2+1LL*p+1)%P),(int)((p3+1LL*p)%P),(int)(3LL*p%P),p,p};
  }else{
   long long key=32LL*p+e;auto it=higher.find(key);
   if(it==higher.end())it=higher.emplace(key,local(p,e)).first;v=it->second;
  }
  for(int k=0;k<6;k++){value[b][k]=1LL*value[core[b]][k]*v[k]%P;sum[k]=(sum[k]+1LL*value[b][k])%P;}
  for(int q:primes){
   if(q>n/b)break;int j=b*q;sp[j]=q;
   if(q==p){ex[j]=e+1;core[j]=core[b];break;}
   ex[j]=1;core[j]=b;
  }
 }
 long long answer=sum[0];
 if(op==1)answer=answer-2LL*sum[1]-sum[2]-sum[3]-2LL*sum[4]+5LL*sum[5];
 cout<<(answer%P+P)%P<<'\n';
}
