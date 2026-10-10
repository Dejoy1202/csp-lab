#include <iostream>
#include <vector>
#include <string>
using namespace std;
long long milli(string s){auto p=s.find('.');return stoll(s.substr(0,p))*1000+stoll(s.substr(p+1));}
int main(){int n,m,k;cin>>n>>m>>k;long long mean=0,variance=0;string s;for(int i=0;i<n;++i){cin>>s;mean+=milli(s);}for(int i=0;i<n;++i){cin>>s;long long v=milli(s);variance+=v*v;}vector<long long>x(k);vector<string>phi(k);for(auto &v:x){cin>>s;v=milli(s);}for(auto &v:phi)cin>>v;long long delta=1000LL*m-mean;int chosen=k-1;for(int i=0;i+1<k;++i){__int128 left=(__int128)2000*delta;long long sum=x[i]+x[i+1];if(left*left<=(__int128)sum*sum*variance){chosen=i;break;}}cout<<phi[chosen]<<'\n';}
