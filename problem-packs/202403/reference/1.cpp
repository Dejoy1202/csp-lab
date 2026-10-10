// Independently implemented for CSP Lab; not copied from an OJ solution.
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n,m; if(!(cin>>n>>m)) return 1;
    vector<int> articles(m+1),total(m+1),last(m+1,-1);
    for(int i=0;i<n;i++) {
        int k; cin>>k;
        while(k--) { int w; cin>>w; total[w]++; if(last[w]!=i) { articles[w]++; last[w]=i; } }
    }
    for(int w=1;w<=m;w++) cout<<articles[w]<<' '<<total[w]<<'\n';
}
