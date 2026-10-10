#include <iostream>
#include <vector>
#include <deque>
#include <algorithm>
using namespace std;
int main(){int n,m;long long T;cin>>n>>m>>T;vector<int>slice(m);for(int &v:slice)cin>>v;vector<int>work(n);vector<vector<bool>>preferred(n,vector<bool>(m));for(int i=0;i<n;++i){int count;cin>>work[i]>>count;while(count--){int cpu;cin>>cpu;preferred[i][cpu-1]=true;}}vector<deque<int>>queues(m);for(int i=0;i<n;++i)queues[i%m].push_back(i);vector<int>running(m,-1);vector<long long>finish(m),first(n,-1),answer(n);long long now=0,rotation=0;int done=0;
while(done<n){
    // Returns use the old correspondence; rotations then precede dispatch.
    for(int cpu=0;cpu<m;++cpu)if(running[cpu]>=0&&finish[cpu]==now){int task=running[cpu];running[cpu]=-1;if(work[task]==0){answer[task]=now-first[task];++done;}else queues[(cpu+rotation)%m].push_back(task);}
    rotation=now/T;
    for(int cpu=0;cpu<m;++cpu)if(running[cpu]<0&&!queues[(cpu+rotation)%m].empty()){int task=queues[(cpu+rotation)%m].front();queues[(cpu+rotation)%m].pop_front();if(first[task]<0)first[task]=now;int speed=preferred[task][cpu]?2:1;int duration=min(slice[cpu],(work[task]+speed-1)/speed);work[task]=max(0,work[task]-duration*speed);running[cpu]=task;finish[cpu]=now+duration;}
    if(done==n)break;
    long long next=(now/T+1)*T;for(int cpu=0;cpu<m;++cpu)if(running[cpu]>=0)next=min(next,finish[cpu]);now=next;
}
for(long long v:answer)cout<<v<<' ';cout<<'\n';}
