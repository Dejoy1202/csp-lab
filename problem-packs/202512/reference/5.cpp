#include <bits/stdc++.h>
using namespace std;
struct Node{int child[2]{},count=0,best=0,version=0;};
struct Cache{uint64_t key=0;int va=0,vb=0,value=0;};
class Repair{
 vector<Node>t{{}};vector<Cache>cache;int top,low,stop;bool trivial;
 int count(int u){return t[u].count;}
 int cross(int a,int b,int bit,int limit){
  if(!a||!b)return count(a)+count(b);
  if(!limit)return max(count(a),count(b));
  uint64_t key=(uint64_t(a)<<32)|unsigned(b);size_t slot=((key^(key>>23))*0x9e3779b97f4a7c15ULL)>>(64-20);
  Cache old=cache[slot];if(old.key==key&&old.va==t[a].version&&old.vb==t[b].version)return old.value;
  int answer;
  if((limit>>bit)&1)
   answer=cross(t[a].child[0],t[b].child[1],bit-1,limit^(1<<bit))+cross(t[a].child[1],t[b].child[0],bit-1,limit^(1<<bit));
  else
   answer=max({count(a),count(b),cross(t[a].child[0],t[b].child[0],bit-1,limit),cross(t[a].child[1],t[b].child[1],bit-1,limit)});
  cache[slot]={key,t[a].version,t[b].version,answer};return answer;
 }
 void pull(int u,int bit){
  if(trivial||bit<top)t[u].best=t[u].count;
  else if(bit>top)t[u].best=max(t[t[u].child[0]].best,t[t[u].child[1]].best);
  else t[u].best=cross(t[u].child[0],t[u].child[1],bit-1,low);
 }
public:
 Repair(long long w){trivial=w>=(1LL<<30);top=trivial?30:63-__builtin_clzll(w);low=trivial?0:int(w-(1LL<<top));stop=trivial?29:__builtin_ctzll(w)-1;cache.resize(1<<20);}
 int cost(int root){return t[root].best;}
 int insert(int u,int x,int bit=29){
  if(!u){u=t.size();t.push_back({});}t[u].count++;t[u].version++;
  if(bit>stop){int d=x>>bit&1;int child=insert(t[u].child[d],x,bit-1);t[u].child[d]=child;}
  pull(u,bit);return u;
 }
 int merge(int a,int b,int bit=29){
  if(!a||!b)return a?a:b;
  if(t[a].count<t[b].count)swap(a,b);
  t[a].count+=t[b].count;t[a].version++;
  if(bit>stop)for(int d=0;d<2;d++){int child=merge(t[a].child[d],t[b].child[d],bit-1);t[a].child[d]=child;}
  pull(a,bit);return a;
 }
};
int main(){
 ios::sync_with_stdio(false);cin.tie(nullptr);
 int n;long long w;cin>>n>>w;Repair solver(w);vector<int>roots(n+1);long long answer=0;
 for(int i=1;i<=n;i++){int m;cin>>m;while(m--){int x;cin>>x;roots[i]=solver.insert(roots[i],x);}answer+=solver.cost(roots[i]);}
 int q;cin>>q;while(q--){
  int op;cin>>op;if(op==3){cout<<answer<<'\n';continue;}
  int u,x;cin>>u>>x;answer-=solver.cost(roots[u]);
  if(op==1)roots[u]=solver.insert(roots[u],x);
  else{answer-=solver.cost(roots[x]);roots[u]=solver.merge(roots[u],roots[x]);roots[x]=0;}
  answer+=solver.cost(roots[u]);
 }
}
