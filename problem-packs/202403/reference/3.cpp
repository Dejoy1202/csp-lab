// Exact fraction-free rank; floating-point tolerances never define the oracle.
#include <bits/stdc++.h>
#include <boost/multiprecision/cpp_int.hpp>
using namespace std;
using boost::multiprecision::cpp_int;
cpp_int gcd_int(cpp_int a,cpp_int b) { if(a<0)a=-a; if(b<0)b=-b; while(b!=0) { cpp_int r=a%b; a=b; b=r; } return a; }
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n; cin>>n;
    while(n--) {
        int m; cin>>m; map<string,int> ids; vector<map<string,int>> compounds(m);
        for(int j=0;j<m;j++) {
            string s; cin>>s;
            for(size_t k=0;k<s.size();) {
                string e; while(k<s.size()&&s[k]>='a'&&s[k]<='z') e+=s[k++];
                int v=0; while(k<s.size()&&isdigit(static_cast<unsigned char>(s[k]))) v=v*10+s[k++]-'0';
                if(!ids.count(e)) ids[e]=ids.size(); compounds[j][e]=v;
            }
        }
        vector<vector<cpp_int>> a(ids.size(),vector<cpp_int>(m));
        for(int j=0;j<m;j++) for(auto [e,v]:compounds[j]) a[ids[e]][j]=v;
        int rank=0;
        for(int col=0;col<m && rank<(int)a.size();col++) {
            int pivot=rank; while(pivot<(int)a.size() && a[pivot][col]==0) pivot++;
            if(pivot==(int)a.size()) continue;
            swap(a[pivot],a[rank]);
            for(int r=rank+1;r<(int)a.size();r++) if(a[r][col]!=0) {
                cpp_int x=a[rank][col],y=a[r][col],g=0;
                for(int c=col;c<m;c++) { a[r][c]=a[r][c]*x-a[rank][c]*y; g=gcd_int(g,a[r][c]); }
                if(g!=0) for(int c=col;c<m;c++) a[r][c]/=g;
            }
            rank++;
        }
        cout<<(rank<m?'Y':'N')<<'\n';
    }
}
