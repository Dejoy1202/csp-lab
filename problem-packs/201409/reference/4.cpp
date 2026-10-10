#include <iostream>
#include <vector>
#include <queue>
using namespace std;
struct Customer {int x,y,quantity;};
int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n,m,k,d;cin>>n>>m>>k>>d;
    vector<int> sources(m);for(int &p:sources){int x,y;cin>>x>>y;p=(x-1)*n+y-1;}
    vector<Customer> clients(k);for(auto &c:clients)cin>>c.x>>c.y>>c.quantity;
    vector<int> distance(n*n,-1);
    while(d--){int x,y;cin>>x>>y;distance[(x-1)*n+y-1]=-2;}
    queue<int> todo;
    for(int p:sources)if(distance[p]==-1){distance[p]=0;todo.push(p);}
    while(!todo.empty()){
        int p=todo.front();todo.pop();int x=p/n,y=p%n;
        int neighbors[4]={p-n,p+n,p-1,p+1};
        bool valid[4]={x>0,x+1<n,y>0,y+1<n};
        for(int dir=0;dir<4;++dir)if(valid[dir]&&distance[neighbors[dir]]==-1){distance[neighbors[dir]]=distance[p]+1;todo.push(neighbors[dir]);}
    }
    long long answer=0;
    for(auto c:clients)answer+=1LL*c.quantity*distance[(c.x-1)*n+c.y-1];
    cout<<answer<<'\n';
}
