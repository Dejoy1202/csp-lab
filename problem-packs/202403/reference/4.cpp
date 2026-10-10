#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int c,m,n; cin>>c>>m>>n;
    map<int,int> active;
    for(int i=0;i<m;i++) { int x,w; cin>>x>>w; active.emplace(x,w); }
    priority_queue<int,vector<int>,greater<int>> pending;
    auto add=[&](map<int,int>::iterator p) { if(++p->second==5) pending.push(p->first); };
    while(n--) {
        int x; cin>>x; auto p=active.find(x); if(p==active.end()) return 2; add(p);
        while(!pending.empty()) {
            int v=pending.top(); pending.pop(); auto cur=active.find(v);
            if(cur==active.end() || cur->second<5) continue;
            auto right=next(cur);
            if(cur!=active.begin()) add(prev(cur));
            if(right!=active.end()) add(right);
            active.erase(cur);
        }
        cout<<active.size()<<'\n';
    }
}
