#include <bits/stdc++.h>
using namespace std;
struct Queue{long long begin,length,next;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,q;cin>>n>>q;vector<vector<Queue>> processes(n+1);map<long long,long long> holes;set<pair<long long,long long>> bySize;long long end=0;
auto eraseHole=[&](long long l){auto it=holes.find(l);bySize.erase({it->second,l});holes.erase(it);};auto addHole=[&](long long l,long long length){holes[l]=length;bySize.insert({length,l});};
while(q--){string op;int p;cin>>op>>p;if(op=="new"){long long length,l;cin>>length;auto it=bySize.lower_bound({length,-1});if(it==bySize.end()){l=end;end+=length;}else{auto [available,start]=*it;l=start;eraseHole(start);if(available>length)addHole(l+length,available-length);}processes[p].push_back({l,length,0});cout<<l<<'\n';}
else if(op=="send"){long long answer=0;for(auto &queue:processes[p]){answer+=queue.begin+queue.next;queue.next=(queue.next+1)%queue.length;}cout<<answer<<'\n';}
else{int i;cin>>i;Queue removed=processes[p][i-1];processes[p].erase(processes[p].begin()+i-1);long long l=removed.begin,length=removed.length;auto right=holes.lower_bound(l);if(right!=holes.begin()){auto left=prev(right);if(left->first+left->second==l){l=left->first;length+=left->second;eraseHole(l);}}right=holes.lower_bound(l);if(right!=holes.end()&&l+length==right->first){long long next=right->first;length+=right->second;eraseHole(next);}if(l+length==end)end=l;else addHole(l,length);}}
}
