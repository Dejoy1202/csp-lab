#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;
int main(){int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;sort(a.begin(),a.end());int s=0;for(int i=1;i<n;++i)s+=a[i]-a[i-1]==1;cout<<s<<'\n';}
