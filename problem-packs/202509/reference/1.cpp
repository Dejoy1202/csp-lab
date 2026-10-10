// CSP Lab: exact hundredth-unit geometry, avoiding floating boundary drift.
#include <bits/stdc++.h>
using namespace std;
long long hundredths(string s){bool neg=s[0]=='-';if(s[0]=='-'||s[0]=='+')s.erase(s.begin());auto p=s.find('.');string whole=s.substr(0,p),fraction=p==string::npos?"":s.substr(p+1);while(fraction.size()<2)fraction+='0';long long v=stoll(whole)*100+stoll(fraction);return neg?-v:v;}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,a;cin>>n>>a;long long r=100LL*a;int inside=0;for(int i=0;i<n;++i){string sx,sy;cin>>sx>>sy;long long x=hundredths(sx),y=hundredths(sy);if(x*x+y*y<=r*r)++inside;}cout<<fixed<<setprecision(9)<<4.0*inside/n<<'\n';}
