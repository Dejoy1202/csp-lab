// Enumerate anti-diagonals with alternating row direction.
#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n;cin>>n;vector<vector<int>>a(n,vector<int>(n));for(auto&r:a)for(int&x:r)cin>>x;bool first=true;for(int sum=0;sum<=2*n-2;++sum){int lo=max(0,sum-n+1),hi=min(n-1,sum);for(int j=lo;j<=hi;++j){int row=(sum&1)==0?hi-(j-lo):j;if(!first)cout<<' ';first=false;cout<<a[row][sum-row];}}cout<<'\n';}
