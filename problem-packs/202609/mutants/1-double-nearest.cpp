// Regression: mathematically equal distances can compare unequal in double.
#include <iostream>
#include <vector>
#include <cmath>
#include <string>
using namespace std;
int main(){
    int n,m,k;cin>>n>>m>>k;
    double u=0,o2=0;
    vector<double>X(k);vector<string>Q(k);
    for(int i=0;i<n;++i){double x;cin>>x;u+=x;}
    for(int i=0;i<n;++i){double x;cin>>x;o2+=x*x;}
    for(auto &x:X)cin>>x;
    for(auto &x:Q)cin>>x;
    double z=(m-u)/sqrt(o2);
    int i=0;while(i<k&&X[i]<z)++i;
    if(i==0){cout<<Q[0];return 0;}
    if(i==k){cout<<Q[k-1];return 0;}
    double a=X[i]-z,b=z-X[i-1];
    if(b<=a)cout<<Q[i-1];else cout<<Q[i];
}
