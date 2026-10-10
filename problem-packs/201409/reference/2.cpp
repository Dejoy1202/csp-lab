#include <iostream>
using namespace std;
int main(){int n;cin>>n;bool grid[100][100]={};while(n--){int a,b,c,d;cin>>a>>b>>c>>d;for(int x=a;x<c;++x)for(int y=b;y<d;++y)grid[x][y]=true;}int s=0;for(auto &row:grid)for(bool painted:row)s+=painted;cout<<s<<'\n';}
