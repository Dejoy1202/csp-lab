// CSP Lab implementation of the public root-selection idea, with iterative indexing,
// range-add visibility, standard ordered sets and small-to-large boundary merging.
// Algorithm source: https://pcs2.roj.ac.cn/problems/shumeng/CSP202605E/
#include <bits/stdc++.h>
#include <cassert>
using namespace std;
constexpr int INF=1000000007;
vector<vector<int>> graph;
int n;
struct TreeIndex {
 vector<int> parent,depth,size,heavy,head,in,out;vector<vector<int>> up;
 TreeIndex():parent(n,-1),depth(n),size(n,1),heavy(n,-1),head(n),in(n),out(n){
  vector<int> order{0};for(size_t j=0;j<order.size();++j){int u=order[j];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;depth[v]=depth[u]+1;order.push_back(v);}}
  for(int i=n-1;i>0;--i){int u=order[i],p=parent[u];size[p]+=size[u];if(heavy[p]<0||size[u]>size[heavy[p]])heavy[p]=u;}
  vector<pair<int,int>> work{{0,0}};int timer=0;
  while(!work.empty()){auto [u,h]=work.back();work.pop_back();for(;u>=0;u=heavy[u]){head[u]=h;in[u]=timer++;for(int v:graph[u])if(v!=parent[u]&&v!=heavy[u])work.push_back({v,v});}}
  for(int u=0;u<n;++u)out[u]=in[u]+size[u];
  int levels=1;while((1<<levels)<=n)++levels;up.assign(levels,vector<int>(n));for(int u=0;u<n;++u)up[0][u]=parent[u]<0?u:parent[u];
  for(int b=1;b<levels;++b)for(int u=0;u<n;++u)up[b][u]=up[b-1][up[b-1][u]];
 }
 bool ancestor(int u,int v)const{return in[u]<=in[v]&&in[v]<out[u];}
 int lift(int u,int steps)const{for(int b=0;steps;steps>>=1,++b)if(steps&1)u=up[b][u];return u;}
 int lca(int u,int v)const{if(ancestor(u,v))return u;if(ancestor(v,u))return v;for(int b=int(up.size())-1;b>=0;--b)if(!ancestor(up[b][u],v))u=up[b][u];return parent[u];}
 int distance(int u,int v)const{return depth[u]+depth[v]-2*depth[lca(u,v)];}
 int toward(int u,int v)const{assert(u!=v);return ancestor(u,v)?lift(v,depth[v]-depth[u]-1):parent[u];}
};
// Active red centers carry the number of strict red ancestors. Only cover=0
// centers are visible. Deleting a red center decreases its descendants' cover.
struct Visibility {
 int length;vector<int> cover,lazy;vector<pair<int,int>> best;
 Visibility(const vector<int>&count,const vector<pair<int,int>>&key):length(count.size()),cover(4*length,INF),lazy(4*length),best(4*length,{-1,-1}){build(1,0,length,count,key);}
 void combine(int p){cover[p]=min(cover[2*p],cover[2*p+1]);best[p]={-1,-1};for(int c:{2*p,2*p+1})if(cover[c]==cover[p])best[p]=max(best[p],best[c]);}
 void build(int p,int l,int r,const vector<int>&count,const vector<pair<int,int>>&key){if(r-l==1){cover[p]=count[l];best[p]=key[l];return;}int m=(l+r)/2;build(2*p,l,m,count,key);build(2*p+1,m,r,count,key);combine(p);}
 void addNode(int p,int d){cover[p]+=d;lazy[p]+=d;}
 void push(int p){if(lazy[p]){addNode(2*p,lazy[p]);addNode(2*p+1,lazy[p]);lazy[p]=0;}}
 void add(int a,int b,int d,int p,int l,int r){if(a>=r||b<=l)return;if(a<=l&&r<=b){addNode(p,d);return;}push(p);int m=(l+r)/2;add(a,b,d,2*p,l,m);add(a,b,d,2*p+1,m,r);combine(p);}
 void add(int a,int b,int d){if(a<b)add(a,b,d,1,0,length);}
 void erase(int x,int p,int l,int r){if(r-l==1){cover[p]=INF;best[p]={-1,-1};return;}push(p);int m=(l+r)/2;if(x<m)erase(x,2*p,l,m);else erase(x,2*p+1,m,r);combine(p);}
 void erase(int x){erase(x,1,0,length);}
 int visible()const{return cover[1]==0?best[1].second:-1;}
};
vector<int> fixedRoot(int root){
 vector<int> parent(n,-1),order{root},minimum(n,INF),entry(n),exit(n),redCount(n);vector<char> active(n),front(n),red(n);vector<vector<int>> byValue(n);
 for(size_t j=0;j<order.size();++j){int u=order[j];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
 deque<int> answer;vector<int> first=graph[root];first.push_back(root);sort(first.begin(),first.end());for(int v:first)answer.push_back(v);int h=answer.front();
 for(int u:order)if(u!=root){for(int v:graph[u])if(v!=parent[u]){minimum[u]=v;active[u]=true;break;}if(active[u]&&minimum[u]<h){red[u]=true;byValue[minimum[u]].push_back(u);}redCount[u]=redCount[parent[u]]+red[parent[u]];}
 int timer=0;vector<pair<int,int>> dfs{{root,0}};while(!dfs.empty()){auto [u,stage]=dfs.back();dfs.pop_back();if(stage){exit[u]=timer;continue;}entry[u]=timer++;dfs.push_back({u,1});for(auto it=graph[u].rbegin();it!=graph[u].rend();++it)if(*it!=parent[u])dfs.push_back({*it,0});}
 vector<int> cover(n,INF);vector<pair<int,int>> keys(n,{-1,-1});for(int u=0;u<n;++u)if(red[u]){cover[entry[u]]=redCount[u];keys[entry[u]]={minimum[u],u};}Visibility visibility(cover,keys);
 set<pair<int,int>> frontier;for(int v:graph[root])if(active[v]){front[v]=true;frontier.insert({minimum[v],v});}
 auto removeRed=[&](int u){if(red[u]){red[u]=false;visibility.erase(entry[u]);visibility.add(entry[u]+1,exit[u],-1);}};
 while(int(answer.size())<n){
  int blocked=visibility.visible(),after=INF;if(blocked>=0){auto it=lower_bound(graph[blocked].begin(),graph[blocked].end(),h);while(it!=graph[blocked].end()&&*it==parent[blocked])++it;if(it!=graph[blocked].end())after=*it;}
  auto it=frontier.upper_bound({h,INF});int available=it==frontier.end()?-1:it->second;
  int u=(available>=0&&(blocked<0||!front[blocked]||(after<INF&&minimum[available]<after)))?available:blocked;
  assert(u>=0&&front[u]&&active[u]);frontier.erase({minimum[u],u});front[u]=false;removeRed(u);int old=h;
  auto split=lower_bound(graph[u].begin(),graph[u].end(),h);for(auto j=make_reverse_iterator(split);j!=graph[u].rend();++j)if(*j!=parent[u])answer.push_front(*j);for(auto j=split;j!=graph[u].end();++j)if(*j!=parent[u])answer.push_back(*j);
  active[u]=false;for(int v:graph[u])if(v!=parent[u]&&active[v]){front[v]=true;frontier.insert({minimum[v],v});}h=answer.front();for(int x=h;x<old;++x)for(int r:byValue[x])removeRed(r);
 }
 return {answer.begin(),answer.end()};
}
struct Fenwick{vector<int> value;Fenwick():value(n+1){}void insert(int p){for(++p;p<=n;p+=p&-p)++value[p];}int before(int p)const{int s=0;for(;p;p-=p&-p)s+=value[p];return s;}int range(int l,int r)const{return before(r)-before(l);}};
// Root-dependent historical red events are active on a subtree or its complement.
// Canonical interval decomposition plus std::set gives point/predecessor queries.
struct Events {
 const TreeIndex &tree;int base=1;vector<set<pair<int,int>>> buckets;vector<int> tag;vector<vector<int>> nodes;vector<char> enabled;
 Events(const TreeIndex&t):tree(t),tag(n,-1),nodes(n),enabled(n){while(base<n)base*=2;buckets.resize(2*base);}
 void interval(int u,int l,int r){for(l+=base,r+=base;l<r;l/=2,r/=2){if(l&1)nodes[u].push_back(l++);if(r&1)nodes[u].push_back(--r);}}
 void toggle(int u,int from,bool on){if(tag[u]<0){tag[u]=from;int first=graph[u][0];bool inside=tree.parent[first]!=u;if(from!=first)inside=!inside;int branch=tree.parent[first]==u?first:u;if(inside)interval(u,tree.in[branch],tree.out[branch]);else{interval(u,0,tree.in[branch]);interval(u,tree.out[branch],n);}}
  assert(tag[u]==from);if(enabled[u]==on)return;enabled[u]=on;for(int p:nodes[u]){if(on)buckets[p].insert({from,u});else buckets[p].erase({from,u});}}
 int predecessor(int root,int h)const{pair<int,int> result{-1,-1};for(int p=base+tree.in[root];p;p/=2){auto it=buckets[p].lower_bound({h,-1});if(it!=buckets[p].begin())result=max(result,*prev(it));}return result.second;}
};
struct Completed {
 vector<int> leader,weight,smallest,second;vector<char> done;vector<set<int>> boundary;vector<set<pair<int,int>>> choices;
 Completed():leader(n),weight(n,1),smallest(n),second(n,INF),done(n),boundary(n),choices(n){iota(leader.begin(),leader.end(),0);iota(smallest.begin(),smallest.end(),0);}
 int find(int u){int r=u;while(leader[r]!=r)r=leader[r];while(u!=r){int v=leader[u];leader[u]=r;u=v;}return r;}
 static int except(int u,int p){if(graph[u][0]!=p)return graph[u][0];return graph[u].size()>1?graph[u][1]:INF;}
 void small(int r,int x){if(x<smallest[r]){second[r]=smallest[r];smallest[r]=x;}else if(x!=smallest[r])second[r]=min(second[r],x);}
 int unite(int u,int v){u=find(u);v=find(v);if(u==v)return u;if(weight[u]+choices[u].size()+boundary[u].size()<weight[v]+choices[v].size()+boundary[v].size())swap(u,v);leader[v]=u;weight[u]+=weight[v];small(u,smallest[v]);small(u,second[v]);boundary[u].merge(boundary[v]);choices[u].merge(choices[v]);return u;}
 void finish(int u){done[u]=true;for(int v:graph[u])if(!done[v]){boundary[u].insert(v);int x=except(v,u);if(x<INF)choices[u].insert({x,v});}
  for(int v:graph[u])if(done[v]){int r=find(v);boundary[r].erase(u);int x=except(u,v);if(x<INF)choices[r].erase({x,u});unite(u,r);}}
 int low(int u,int root){u=find(u);int value=smallest[u]==root?second[u]:smallest[u];if(!boundary[u].empty())value=min(value,*boundary[u].begin());return value;}
 int next(int u,int h){u=find(u);auto it=choices[u].upper_bound({h,INF});return it==choices[u].end()?-1:it->second;}
};
struct RootSearch {
 TreeIndex tree;Events events;Completed completed;Fenwick prefix;
 set<int> candidates,pending;vector<int> direction,component,record,recordId,eventTag,eventId;vector<char> visited,marked,consumed,eventOn;
 vector<pair<int,int>> deferred;vector<int> restore;vector<set<int>> unused;
 int clock=0,activeRoot=-1,head=INF,cut=0,block=-1,blockFloor=0,last=-1;bool alive=false,rootFinished=false;vector<int> prefixOrder;
 RootSearch():events(tree),direction(n,-1),component(n),record(n),recordId(n,-1),eventTag(n,-1),eventId(n,-1),visited(n),marked(n),consumed(n),eventOn(n),unused(n){iota(component.begin(),component.end(),0);iota(record.begin(),record.end(),0);for(int u=0;u<n;++u){candidates.insert(u);pending.insert(u);unused[u].insert(graph[u].begin(),graph[u].end());}}
 int componentRoot(int u){int r=u;while(component[r]!=r)r=component[r];while(u!=r){int v=component[u];component[u]=r;u=v;}return r;}
 bool has(int u)const{return u>=0&&candidates.count(u);}
 int pathMarks(int u,int v)const{int s=0;while(tree.head[u]!=tree.head[v]){if(tree.depth[tree.head[u]]<tree.depth[tree.head[v]])swap(u,v);s+=prefix.range(tree.in[tree.head[u]],tree.in[u]+1);u=tree.parent[tree.head[u]];}if(tree.depth[u]>tree.depth[v])swap(u,v);return s+prefix.range(tree.in[u],tree.in[v]+1);}
 bool valid(int u,int target=-1){if(has(u))return true;int p=direction[u];if(p<0)return false;if(direction[p]<0)return true;int count=pathMarks(p,componentRoot(u));if(!count)return true;return count==1&&marked[p]&&!prefixOrder.empty()&&prefixOrder.back()==p&&(target<0||tree.distance(target,u)<=2);}
 void orient(int u,int p){vector<pair<int,int>> todo{{u,p}};while(!todo.empty()){auto [x,f]=todo.back();todo.pop_back();if(!has(x))continue;direction[x]=f;component[componentRoot(x)]=componentRoot(f);candidates.erase(x);for(int y:graph[x])if(y!=f&&has(y))todo.push_back({y,x});}}
 bool eligible(int u,int from)const{return from==graph[u][0]||(graph[u].size()>1&&from==graph[u][1]);}
 void enable(int u,int from){if(completed.done[u]||eventOn[u]||!eligible(u,from))return;events.toggle(u,from,true);eventOn[u]=true;}
 void disable(int u){if(eventOn[u]){events.toggle(u,eventTag[u],false);eventOn[u]=false;}}
 void restoreEvents(){for(int u:restore)enable(u,eventTag[u]);restore.clear();for(auto [u,f]:deferred)enable(u,f);deferred.clear();}
 void fixPrefix(int x,int from=-1){if(x<0)return;if(!marked[x]){marked[x]=true;prefixOrder.push_back(x);prefix.insert(tree.in[x]);if(from>=0){int id=clock++;record[x]=from;recordId[x]=id;if(eligible(x,from)){eventTag[x]=from;eventId[x]=id;if(alive)deferred.push_back({x,from});else enable(x,from);}}}
  else if(from>=0&&record[x]<from&&from<x&&!(alive&&from==activeRoot)&&!marked[from]&&recordId[x]>=0){marked[from]=true;prefixOrder.push_back(from);prefix.insert(tree.in[from]);record[from]=record[x];record[x]=from;recordId[from]=recordId[x];}}
 void consume(int x){if(consumed[x])return;consumed[x]=true;for(int u:graph[x])unused[u].erase(x);}
 int parentOf(int u)const{return u==activeRoot?-1:tree.toward(u,activeRoot);}
 int childMinimum(int u)const{int p=parentOf(u);return graph[u][0]!=p?graph[u][0]:(graph[u].size()>1?graph[u][1]:INF);}
 bool open(int u){if(u==activeRoot||completed.done[u])return false;int p=parentOf(u);return p>=0&&completed.done[p]&&completed.find(p)==completed.find(activeRoot);}
 void finish(int u){if(!completed.done[u]){assert(consumed[u]&&unused[u].empty());disable(u);completed.finish(u);}head=min(head,completed.low(u,activeRoot));}
 void begin(int root){if(alive)return;restoreEvents();activeRoot=root;alive=true;cut=clock;rootFinished=false;block=-1;head=min(root,graph[root][0]);}
 int peek(){while(true){if(!rootFinished){int x=consumed[activeRoot]?INF:activeRoot;if(!unused[activeRoot].empty())x=min(x,*unused[activeRoot].begin());if(x<INF)return x;finish(activeRoot);rootFinished=true;}
  if(block>=0){auto it=unused[block].lower_bound(blockFloor);if(it!=unused[block].end())return *it;finish(block);block=-1;}
  int red=head>0?events.predecessor(activeRoot,head):-1,after=INF;if(red>=0){assert(eventId[red]<cut&&childMinimum(red)==eventTag[red]);auto it=lower_bound(graph[red].begin(),graph[red].end(),head);while(it!=graph[red].end()&&*it==parentOf(red))++it;if(it!=graph[red].end())after=*it;}
  int first=completed.next(activeRoot,head);int u=(first>=0&&(red<0||!open(red)||(after<INF&&childMinimum(first)<after)))?first:red;if(u<0)return INF;assert(open(u));block=u;blockFloor=head;int value=childMinimum(u);if(value<head){if(eventId[u]>=0&&eventId[u]<cut&&eventTag[u]==value&&eventOn[u]){disable(u);restore.push_back(u);}head=value;}
 }}
 int compareNext(int x){if(!alive)return -1;int y=peek();if(y==INF)return -1;if(y<x)return activeRoot;if(y>x){alive=false;restoreEvents();}else consume(y);return -1;}
 int processRoot(int x){for(int y:graph[x])if(visited[y]&&direction[y]<0){assert(has(y)&&last==y);begin(y);}pending.erase(x);
  while(!pending.empty()){int y=*pending.begin();if(!valid(y,x)){pending.erase(y);continue;}int winner=compareNext(y);if(winner>=0)return winner;int d=tree.distance(x,y);
   if(d>=3){int u=tree.toward(x,y),v=tree.toward(u,y);if(!has(v)){pending.erase(y);continue;}if(last>=0&&u!=last){fixPrefix(x,last);last=-1;}orient(u,v);fixPrefix(direction[x],x);}
   else if(d==2){int u=tree.toward(x,y);if(!has(u)){pending.erase(y);continue;}if(last>=0&&u!=last)fixPrefix(x,last);orient(x,u);fixPrefix(direction[x],x);}
   else{if(last>=0&&y!=last)fixPrefix(x,last);for(int v:graph[x])if(v!=y&&direction[v]!=x)orient(v,x);last=x;}break;
  }return -1;
 }
 vector<int> solve(){while(candidates.size()>2){assert(!pending.empty());int x=*pending.begin();visited[x]=true;consume(x);
   if(has(x)){int winner=processRoot(x);if(winner>=0)return fixedRoot(winner);continue;}
   if(!valid(x)){pending.erase(x);continue;}fixPrefix(direction[x],x);pending.erase(x);if(has(direction[x])){while(!pending.empty()){int y=*pending.begin();if(!valid(y,x)){pending.erase(y);continue;}int winner=compareNext(y);if(winner>=0)return fixedRoot(winner);if(tree.distance(x,y)>=3){int u=tree.toward(x,y),v=tree.toward(u,y);if(u!=direction[x]){pending.erase(y);continue;}orient(u,v);}break;}}
  }
  vector<int> result(n,INF);for(int root:candidates)result=min(result,fixedRoot(root));if(alive)result=min(result,fixedRoot(activeRoot));return result;
 }
};
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);cin>>n;graph.resize(n);for(int i=1;i<n;++i){int u,v;cin>>u>>v;--u;--v;graph[u].push_back(v);graph[v].push_back(u);}for(auto &row:graph)sort(row.begin(),row.end());RootSearch search;auto answer=search.solve();for(int i=0;i<n;++i)cout<<answer[i]+1<<(i+1==n?'\n':' ');}
