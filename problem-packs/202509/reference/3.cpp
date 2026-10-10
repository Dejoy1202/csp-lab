// CSP Lab: array tree and circular dynamic table; no recursive field decoding.
#include <bits/stdc++.h>
using namespace std;
struct Node{int child[2]={-1,-1};char letter=0;};vector<Node> tree;string description;int cursor=0;
int build(){int id=tree.size();tree.emplace_back();char tag=description[cursor++];if(tag=='1')tree[id].letter=description[cursor++];else{int l=build(),r=build();tree[id].child[0]=l;tree[id].child[1]=r;}return id;}
string decode(const string &s){if(s[0]!='H')return s;if(s.size()>1&&s[1]=='H')return s.substr(1);vector<int> bytes;for(size_t i=1;i<s.size();i+=2)bytes.push_back(stoi(s.substr(i,2),nullptr,16));int padding=bytes.back();bytes.pop_back();int bits=int(bytes.size()*8)-padding,state=0;string out;for(int i=0;i<bits;++i){int direction=(bytes[i/8]>>(7-i%8))&1;state=tree[state].child[direction];if(tree[state].letter){out+=tree[state].letter;state=0;}}return out;}
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int S,D,N;cin>>S>>D;vector<pair<string,string>> fixed(S),ring(D);for(auto &entry:fixed)cin>>entry.first>>entry.second;cin>>description;build();cin>>N;int head=0,count=0;
auto lookup=[&](int index)->pair<string,string>{if(index<=S)return fixed[index-1];return ring[(head+index-S-1)%D];};
while(N--){int type,index;cin>>type>>index;pair<string,string> field;if(type==1)field=lookup(index);else{string token;if(index==0){cin>>token;field.first=decode(token);}else field.first=lookup(index).first;cin>>token;field.second=decode(token);}cout<<field.first<<": "<<field.second<<'\n';if(type==2){head=(head+D-1)%D;ring[head]=field;count=min(D,count+1);}}}
