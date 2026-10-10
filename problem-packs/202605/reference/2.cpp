#include <bits/stdc++.h>
using namespace std;
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);long long n;int k,m;cin>>n>>k>>m;
auto feasible=[&](long long count){long long left=n;for(int day=0;day<m;++day){left-=( (__int128)left*k+99)/100;left-=count;if(left<0)return false;}return true;};
long long low=0,high=1000000000LL;while(low<high){long long middle=(low+high+1)/2;if(feasible(middle))low=middle;else high=middle-1;}cout<<low<<'\n';}
