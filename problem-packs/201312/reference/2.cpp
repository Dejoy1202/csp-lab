#include <bits/stdc++.h>
using namespace std;
int main(){string s;cin>>s;int k=0,sum=0;for(int i=0;i<12;i++)if(isdigit(s[i]))sum+=(++k)*(s[i]-'0');int r=sum%11;char c=r==10?'X':char('0'+r);if(s[12]==c)cout<<"Right\n";else{s[12]=c;cout<<s<<'\n';}}
