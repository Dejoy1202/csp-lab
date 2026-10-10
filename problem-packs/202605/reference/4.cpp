#include <bits/stdc++.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
using namespace std;
struct FastInput {
 unsigned char buffer[65536]; size_t position=0,length=0;
 int read(){if(position==length){length=fread(buffer,1,sizeof(buffer),stdin);position=0;if(!length)return EOF;}return buffer[position++];}
 int next(){int c=read();while(c<=32&&c!=EOF)c=read();int x=0;while(c>32&&c!=EOF){x=x*10+c-'0';c=read();}return x;}
};
int main(){
#ifdef _WIN32
 _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
 FastInput in;int n=in.next(),q=in.next();vector<unsigned> prefix(n+2);vector<pair<unsigned,int>> keys;keys.reserve(n);for(int i=1;i<=n;++i){prefix[i]=prefix[i-2<0?0:i-2]^unsigned(in.next());keys.push_back({prefix[i],i});}
 sort(keys.begin(),keys.end());vector<int> end(n+3,n+1);vector<pair<unsigned,int>> ordered[2];for(auto [x,i]:keys)ordered[i%2].push_back({x,i});
 for(int parity=0;parity<2;++parity){auto &v=ordered[parity];for(int j=0;j<(int)v.size();++j){int i=v[j].second;unsigned target=prefix[i>=2?i-2:0];auto it=lower_bound(v.begin(),v.end(),pair<unsigned,int>{target,i});if(it!=v.end()&&it->first==target)end[i]=it->second;}}
 // Taking the earliest finishing winning interval is optimal even when its start skips losing singletons.
 for(int i=n;i>=1;--i)end[i]=min(end[i],end[i+1]);
 int levels=1;while((1<<levels)<=n)++levels;vector<vector<int>> jump(levels,vector<int>(n+3,n+2));for(int i=1;i<=n;++i)jump[0][i]=end[i]+1;
 for(int b=1;b<levels;++b)for(int i=1;i<=n;++i)jump[b][i]=jump[b-1][jump[b-1][i]];
 string output;output.reserve(q*4);while(q--){int l=in.next(),r=in.next(),answer=0;for(int b=levels-1;b>=0;--b)if(jump[b][l]<=r+1){answer+=1<<b;l=jump[b][l];}output+=to_string(answer);output+='\n';}fwrite(output.data(),1,output.size(),stdout);}
