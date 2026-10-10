// CSP Lab: each window contributes an interval; merge sorted intervals.
#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,L;cin>>n>>L;vector<vector<int>> a(n,vector<int>(n));for(auto &row:a)for(int &v:row)cin>>v;
const string pattern[5]={"111111111","100100101","100111110","100001100","111111100"};vector<pair<int,int>> intervals;
for(int top=0;top+5<=n;++top)for(int left=0;left+9<=n;++left){int low=1,high=L-1;for(int r=0;r<5;++r)for(int c=0;c<9;++c){if(pattern[r][c]=='1')high=min(high,a[top+r][left+c]);else low=max(low,a[top+r][left+c]+1);}if(low<=high)intervals.emplace_back(low,high);}
sort(intervals.begin(),intervals.end());int printed=-1;for(auto [low,high]:intervals){for(int k=max(low,printed+1);k<=high;++k)cout<<k<<'\n';printed=max(printed,high);}}
