// Independent ordinary Eratosthenes factorization, not the reference linear recurrence.
#include <bits/stdc++.h>
using namespace std;const int MOD=998244353;
using Vec=array<int,6>;
Vec factor(int p,int e){
 vector<int>powers(3*e+1,1);for(int j=1;j<=3*e;j++)powers[j]=1LL*powers[j-1]*p%MOD;
 Vec out{};auto add=[&](int k,int exponent){out[k]=(out[k]+1LL*powers[exponent])%MOD;};
 // Nonnegative exponents c,d of C,E; all local constraints tested literally.
 for(int c=0;c<=2*e;c++)for(int d=0;d<=2*e;d++)if(c+d<=3*e){
  int z=3*e-c-d;add(0,z);
  if(c==e)add(1,z);
  if(c==d)add(2,z);
  if(c+d==2*e)add(3,z);
  if(d==3*e-2*c)add(4,z);
  if(c==e&&d==e)add(5,z);
 }
 return out;
}
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);int op,n;cin>>op>>n;vector<int>spf(n+1);
 for(int p=2;p<=n;p++)if(!spf[p]){spf[p]=p;if(p<=n/p)for(int j=p*p;j<=n;j+=p)if(!spf[j])spf[j]=p;}
 unordered_map<long long,Vec>cache;array<long long,6>sum{};sum.fill(1);
 for(int b=2;b<=n;b++){
  int x=b;Vec v;v.fill(1);
  while(x>1){
   int p=spf[x],e=0;do{x/=p;e++;}while(x%p==0);
   Vec part;
   if(e==1){long long p2=1LL*p*p%MOD,p3=p2*p%MOD;part={(int)((p3+2*p2+3LL*p+2)%MOD),(int)((p2+p+1)%MOD),(int)((p3+p)%MOD),(int)(3LL*p%MOD),p,p};}
   else{long long key=32LL*p+e;if(!cache.count(key))cache[key]=factor(p,e);part=cache[key];}
   for(int k=0;k<6;k++)v[k]=1LL*v[k]*part[k]%MOD;
  }
  for(int k=0;k<6;k++)sum[k]=(sum[k]+v[k])%MOD;
 }
 long long ans=sum[0];if(op)ans-=2*sum[1]+sum[2]+sum[3]+2*sum[4]-5*sum[5];cout<<(ans%MOD+MOD)%MOD<<'\n';
}
