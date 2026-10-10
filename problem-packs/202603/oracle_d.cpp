// Independent sqrt decomposition oracle. Whole-block updates only accumulate
// digit offsets; moments are rebuilt from explicit elements after partial updates.
#include <bits/stdc++.h>
using namespace std;using U=uint64_t;
struct Op{int t,l,r;U v;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,q;U k;cin>>n>>q>>k;vector<U>values(n);U high=0;for(auto &v:values){cin>>v;high=max(high,v);}vector<Op>ops(q);for(auto &o:ops){cin>>o.t>>o.l>>o.r;--o.l;--o.r;o.v=0;if(o.t==1){cin>>o.v;high=max(high,o.v);}}
int d=1;for(U v=high;v>=k;v/=k)++d;int B=700,count=(n+B-1)/B;vector<vector<U>>a(n,vector<U>(d)),shift(count,vector<U>(d)),sum(count,vector<U>(d)),product(count,vector<U>(d));vector<U>square(count);for(int i=0;i<n;++i)for(int j=0;j<d;++j){a[i][j]=values[i]%k;values[i]/=k;}
auto rebuild=[&](int block){fill(sum[block].begin(),sum[block].end(),0);fill(product[block].begin(),product[block].end(),0);square[block]=0;for(int i=block*B;i<min(n,(block+1)*B);++i){U low=a[i][0];square[block]=(square[block]+low*low)%k;for(int j=0;j<d;++j){sum[block][j]=(sum[block][j]+a[i][j])%k;product[block][j]=(product[block][j]+a[i][j]*low)%k;}}};
auto materialize=[&](int block){for(int i=block*B;i<min(n,(block+1)*B);++i)for(int j=0;j<d;++j)a[i][j]=(a[i][j]+shift[block][j])%k;fill(shift[block].begin(),shift[block].end(),0);};for(int b=0;b<count;++b)rebuild(b);
for(auto op:ops){vector<U>digits(d),answer(d);if(op.t==1)for(int j=0;j<d;++j){digits[j]=op.v%k;op.v/=k;}for(int block=op.l/B;block<=op.r/B;++block){int l=max(op.l,block*B),r=min(op.r,min(n,(block+1)*B)-1);bool full=l==block*B&&r==min(n,(block+1)*B)-1;if(op.t==1){if(full){for(int j=0;j<d;++j)shift[block][j]=(shift[block][j]+digits[j])%k;}else{materialize(block);for(int i=l;i<=r;++i)for(int j=0;j<d;++j)a[i][j]=(a[i][j]+digits[j])%k;rebuild(block);}}
else if(full){U len=r-l+1,low=shift[block][0],s0=sum[block][0];U triangular=(square[block]+s0+2*low*s0+(len*low%k)*(low+1))%k;answer[0]=(answer[0]+triangular*((k+1)/2))%k;for(int j=1;j<d;++j){U h=shift[block][j];U value=(product[block][j]+sum[block][j]*(low+1)+h*s0+(len*h%k)*(low+1))%k;answer[j]=(answer[j]+value)%k;}}
else{for(int i=l;i<=r;++i){U low=(a[i][0]+shift[block][0])%k;answer[0]=(answer[0]+low*(low+1)/2)%k;for(int j=1;j<d;++j){U h=(a[i][j]+shift[block][j])%k;answer[j]=(answer[j]+h*(low+1))%k;}}}}
if(op.t==2){U result=0,power=1;for(U digit:answer){result+=digit*power;power*=k;}cout<<result<<'\n';}}
}
