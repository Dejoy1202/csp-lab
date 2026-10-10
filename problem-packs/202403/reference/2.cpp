#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n,m; cin>>n>>m; set<string> a,b;
    auto read=[](int k,set<string>& out) {
        while(k--) { string s; cin>>s; for(char &c:s) if(c>='A'&&c<='Z') c+=32; out.insert(s); }
    };
    read(n,a); read(m,b); size_t common=0;
    for(const auto& s:a) common+=b.count(s);
    cout<<common<<'\n'<<a.size()+b.size()-common<<'\n';
}
