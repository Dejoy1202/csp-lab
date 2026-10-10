#include <bits/stdc++.h>
using namespace std;
struct Process{char type;int start,patience;vector<pair<int,int>> tasks;int cursor=0,left=0,since=0;bool released=false,finished=false;long long income=0;int stopped=-1;};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,m;cin>>n>>m;vector<Process> p(n);for(auto &a:p){int k;cin>>a.type>>a.start;if(a.type!='X')cin>>a.patience;else a.patience=0;cin>>k;a.tasks.resize(k);for(auto &t:a.tasks)cin>>t.first>>t.second;}
vector<int> owner(m+1,-1);
for(int now=1;;++now){
 vector<vector<int>> requests(m+1),steals(m+1);vector<bool> running(n,false);
 for(int i=0;i<n;++i){auto &a=p[i];if(a.finished||now<a.start)continue;if(a.left){running[i]=true;continue;}if(!a.since){a.since=now;a.released=false;}
 int resource=a.tasks[a.cursor].first;
 if(a.type=='C'&&now>=a.since+a.patience)steals[resource].push_back(i);else requests[resource].push_back(i);
 }
 for(int resource=1;resource<=m;++resource){auto &forced=steals[resource];if(!forced.empty()){
  owner[resource]=forced.back();for(int i:forced){p[i].left=p[i].tasks[p[i].cursor].second;running[i]=true;}
 }else if(owner[resource]<0&&!requests[resource].empty()){
  int i=requests[resource].front();owner[resource]=i;p[i].left=p[i].tasks[p[i].cursor].second;running[i]=true;
 }}
 for(int i=0;i<n;++i){auto &a=p[i];if(a.finished||now<a.start||running[i])continue;if(a.type=='B'&&now>=a.since+a.patience-1){a.left=a.tasks[a.cursor].second;running[i]=true;}}
 for(int i=0;i<n;++i)if(running[i]){for(int x:owner)p[i].income+=(x==i);}
 vector<bool> drop(n,false);bool future=false;
 for(int i=0;i<n;++i){auto &a=p[i];if(a.finished)continue;if(now<a.start){future=true;continue;}
  if(running[i]){future=true;if(--a.left==0){++a.cursor;a.since=0;if(a.cursor==(int)a.tasks.size()){a.finished=true;a.stopped=now;drop[i]=true;}}}
  else if(a.type=='A'&&!a.released&&now>=a.since+a.patience-1){drop[i]=true;a.released=true;future=true;}
  else if(a.type=='A'&&!a.released)future=true;
  else if(a.type=='B'||a.type=='C')future=true;
 }
 for(int x=1;x<=m;++x)if(owner[x]>=0&&drop[owner[x]])owner[x]=-1;
 // A waiting process can still progress if its requested resource is free next segment.
 for(int i=0;i<n;++i)if(!p[i].finished&&now>=p[i].start&&!p[i].left&&owner[p[i].tasks[p[i].cursor].first]<0)future=true;
 if(!future)break;
}
for(auto &a:p)cout<<a.income<<' '<<(a.stopped<0?-1:a.stopped-a.start+1)<<'\n';}
