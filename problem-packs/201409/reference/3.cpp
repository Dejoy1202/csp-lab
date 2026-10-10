#include <iostream>
#include <string>
#include <cctype>
using namespace std;
string normalized(string s){for(char &c:s)c=tolower((unsigned char)c);return s;}
int main(){string pattern,text;int option,n;cin>>pattern>>option>>n;if(!option)pattern=normalized(pattern);while(n--){cin>>text;string search=option?text:normalized(text);if(search.find(pattern)!=string::npos)cout<<text<<'\n';}}
