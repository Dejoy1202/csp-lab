// Digit moment method; the mathematical identities are also explained at
// https://pcs2.roj.ac.cn/problems/shumeng/CSP202603D/ . Implementation by CSP Lab.
#include <bits/stdc++.h>
using namespace std;using U=uint64_t;
struct Op{int type,l,r;U value;};
struct Tree{int n,d,width;U k;vector<uint32_t> moments,lazy;
Tree(vector<U>&a,int digits,U base):n(a.size()),d(digits),width(2*digits),k(base),moments((4*n+8)*width),lazy((4*n+8)*d){build(1,0,n-1,a);}
uint32_t* s(int p){return &moments[(size_t)p*width];}uint32_t* tag(int p){return &lazy[(size_t)p*d];}
void pull(int p){auto a=s(p),b=s(p*2),c=s(p*2+1);for(int j=0;j<width;++j)a[j]=(U(b[j])+c[j])%k;}
void build(int p,int l,int r,vector<U>&a){if(l==r){U x=a[l],first=x%k;auto z=s(p);z[0]=first;z[1]=first*first%k;for(int j=1;j<d;++j){x/=k;U digit=x%k;z[2*j]=digit;z[2*j+1]=digit*first%k;}return;}int mid=(l+r)/2;build(p*2,l,mid,a);build(p*2+1,mid+1,r,a);pull(p);}
void apply(int p,int length,const uint32_t* c){auto a=s(p),t=tag(p);U old=a[0],low=c[0],size=length%k;
for(int j=1;j<d;++j){U higher=c[j],previous=a[2*j];a[2*j+1]=(a[2*j+1]+low*previous+higher*old+(size*higher%k)*low)%k;a[2*j]=(previous+size*higher)%k;}
a[1]=(a[1]+2*low*old+(size*low%k)*low)%k;a[0]=(old+size*low)%k;for(int j=0;j<d;++j)t[j]=(U(t[j])+c[j])%k;}
void push(int p,int l,int r){auto t=tag(p);if(l==r)return;bool pending=false;for(int j=0;j<d;++j)pending|=t[j]!=0;if(!pending)return;int mid=(l+r)/2;apply(p*2,mid-l+1,t);apply(p*2+1,r-mid,t);fill(t,t+d,0);}
void change(int p,int l,int r,int ql,int qr,const uint32_t* c){if(ql<=l&&r<=qr){apply(p,r-l+1,c);return;}push(p,l,r);int mid=(l+r)/2;if(ql<=mid)change(p*2,l,mid,ql,qr,c);if(qr>mid)change(p*2+1,mid+1,r,ql,qr,c);pull(p);}
void query(int p,int l,int r,int ql,int qr,vector<U>&out){if(ql<=l&&r<=qr){auto a=s(p);out[0]=(out[0]+((U(a[0])+a[1])%k)*((k+1)/2))%k;for(int j=1;j<d;++j)out[j]=(out[j]+a[2*j]+U(a[2*j+1]))%k;return;}push(p,l,r);int mid=(l+r)/2;if(ql<=mid)query(p*2,l,mid,ql,qr,out);if(qr>mid)query(p*2+1,mid+1,r,ql,qr,out);}
};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;U k;cin>>n>>m>>k;vector<U>a(n);U maximum=0;for(auto &x:a){cin>>x;maximum=max(maximum,x);}vector<Op>ops(m);for(auto &op:ops){cin>>op.type>>op.l>>op.r;op.value=0;if(op.type==1){cin>>op.value;maximum=max(maximum,op.value);}}int d=1;for(U x=maximum;x>=k;x/=k)++d;Tree tree(a,d,k);for(auto op:ops){if(op.type==1){vector<uint32_t>digits(d);for(int j=0;j<d;++j){digits[j]=op.value%k;op.value/=k;}tree.change(1,0,n-1,op.l-1,op.r-1,digits.data());}else{vector<U>digits(d);tree.query(1,0,n-1,op.l-1,op.r-1,digits);U answer=0,power=1;for(U digit:digits){answer+=digit*power;power*=k;}cout<<answer<<'\n';}}}
