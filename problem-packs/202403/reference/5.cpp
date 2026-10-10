// Iterative Euler traversal + intrusive child lists + Fenwick range updates.
#include <bits/stdc++.h>
using namespace std;
struct Fenwick {
    vector<int> b; Fenwick(int n):b(n+3){}
    void add(int p,int v){for(;p<(int)b.size();p+=p&-p)b[p]+=v;}
    int get(int p){int v=0;for(;p;p-=p&-p)v+=b[p];return v;}
};
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n,m; cin>>n>>m;
    vector<int> head(n+1),tail(n+1),sibling(n+1),cnt(n+1),tin(n+1),tout(n+1),depth(n+1);
    vector<long long> data(n+1);
    for(int v=2;v<=n;v++) { int p;cin>>p;if(!head[p])head[p]=v;else sibling[tail[p]]=v;tail[p]=v;cnt[p]++; }
    for(int v=1;v<=n;v++)cin>>data[v];
    vector<pair<int,bool>> stack; stack.emplace_back(1,false); int timer=0; depth[1]=1;
    while(!stack.empty()) {
        auto [v,exit]=stack.back();stack.pop_back();
        if(exit){tout[v]=timer;continue;}
        tin[v]=++timer;stack.emplace_back(v,true);
        for(int ch=head[v];ch;ch=sibling[ch]) {depth[ch]=depth[v]+1;stack.emplace_back(ch,false);}
    }
    Fenwick bit(n);
    while(m--) {
        int op,x;cin>>op>>x;
        if(op==2) {cout<<depth[x]+bit.get(tin[x])<<'\n';continue;}
        // Detach the OLD child list. Newly promoted grandchildren wait for the next operation.
        int child=head[x]; head[x]=tail[x]=cnt[x]=0;
        while(child) {
            int next_child=sibling[child];
            data[x]+=data[child]; bit.add(tin[child],-1); bit.add(tout[child]+1,1);
            if(head[child]) {
                if(tail[x])sibling[tail[x]]=head[child];else head[x]=head[child];
                tail[x]=tail[child];cnt[x]+=cnt[child];
            }
            child=next_child;
        }
        if(tail[x])sibling[tail[x]]=0;
        cout<<cnt[x]<<' '<<data[x]<<'\n';
    }
}
