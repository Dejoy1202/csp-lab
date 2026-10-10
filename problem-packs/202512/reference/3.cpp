#include <bits/stdc++.h>
using namespace std;
struct Op{array<int,6>v;};
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);
 int z;cin>>z;vector<string>a(z);for(auto&s:a)cin>>s;
 int len,t;cin>>len>>t;vector<Op>ops(t);for(auto&o:ops)for(int&x:o.v)cin>>x;
 int turn=0;
 auto pos=[&](int row,int col){
  for(int i=0;i<turn;i++){int next=z-1-col;col=row;row=next;}
  return pair<int,int>(row,col);
 };
 auto read=[&](int r,int c){auto [x,y]=pos(r,c);return a[x][y];};
 auto write=[&](int r,int c,char value){auto[x,y]=pos(r,c);a[x][y]=value;};
 for(int i=t-1;i>=0;i--){
  auto v=ops[i].v;
  if(v[0]==1){
   turn=(turn+v[5])%4; // inverse of a whole-image CCW rotation
   int u=v[1]-1,w=v[2]-1,L=v[3],steps=(4-v[4]/90)%4;
   char tmp[10][10];for(int r=0;r<L;r++)for(int c=0;c<L;c++)tmp[r][c]=read(u+r,w+c);
   for(int r=0;r<L;r++)for(int c=0;c<L;c++){
    int x=r,y=c;for(int k=0;k<steps;k++){int next=y;y=L-1-x;x=next;}
    write(u+x,w+y,tmp[r][c]);
   }
  }else{
   int u=v[1]-1,d=v[2]-1,l=v[3]-1,r=v[4]-1;
   char tmp[10][10];for(int x=u;x<=d;x++)for(int y=l;y<=r;y++)tmp[x-u][y-l]=read(x,y);
   for(int x=u;x<=d;x++)for(int y=l;y<=r;y++)
    write(v[5]==1?u+d-x:x,v[5]==-1?l+r-y:y,tmp[x-u][y-l]);
  }
 }
 int n=0,m=0;for(int r=0;r<z;r++)for(int c=0;c<z;c++)if(read(r,c)!='?'){n=max(n,r+1);m=max(m,c+1);}
 cout<<n<<' '<<m<<'\n';for(int r=0;r<n;r++){for(int c=0;c<m;c++)cout<<read(r,c);cout<<'\n';}
}
