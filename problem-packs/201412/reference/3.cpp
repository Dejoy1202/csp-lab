// Integer cents; ordered price sweep, inclusive orders and 64-bit volume.
#include <bits/stdc++.h>
using namespace std;
struct Order{string type;int price;long long quantity;bool active;};
int cents(string s){auto p=s.find('.');return stoi(s.substr(0,p))*100+stoi(s.substr(p+1));}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);vector<Order>orders(1);string type;while(cin>>type){if(type=="cancel"){int line;cin>>line;orders[line].active=false;orders.push_back({type,0,0,false});}else{string p;long long s;cin>>p>>s;orders.push_back({type,cents(p),s,true});}}
map<int,pair<long long,long long>>levels;long long buyers=0,sellers=0;for(auto&o:orders)if(o.active){if(o.type=="buy"){levels[o.price].first+=o.quantity;buyers+=o.quantity;}else levels[o.price].second+=o.quantity;}
long long best=-1;int chosen=0;for(auto [p,amount]:levels){sellers+=amount.second;long long volume=min(buyers,sellers);if(volume>=best){best=volume;chosen=p;}buyers-=amount.first;}if(best<0)best=0;cout<<chosen/100<<'.'<<setw(2)<<setfill('0')<<chosen%100<<' '<<best<<'\n';}
