#include <iostream>
#include <vector>
#include <functional>
#include <queue>
using namespace std;
const long long MOD=1000000007;
using Matrix=vector<vector<long long>>;
Matrix product(const Matrix &a,const Matrix &b){
    int size=a.size();Matrix out(size,vector<long long>(size));
    for(int i=0;i<size;++i)for(int k=0;k<size;++k)if(a[i][k])for(int j=0;j<size;++j)if(b[k][j])
        out[i][j]=(out[i][j]+a[i][k]*b[k][j])%MOD;
    return out;
}
int main(){
    unsigned long long n;int m;cin>>n>>m;
    if((n%3)*(m%3)%3){cout<<0<<'\n';return 0;}
    const int states=1<<m,full=states-1;
    vector<vector<int>> cover(m);
    // Enumerate three cells of each 2x2 block instead of four special-case rules.
    for(int left=0;left+1<m;++left){
        int cells[4]={left,left+1,m+left,m+left+1};
        for(int missing=0;missing<4;++missing){
            int piece=0;for(int j=0;j<4;++j)if(j!=missing)piece|=1<<cells[j];
            for(int j=0;j<m;++j)if(piece&(1<<j))cover[j].push_back(piece);
        }
    }
    Matrix transfer(states,vector<long long>(states));
    for(int entry=0;entry<states;++entry){
        function<void(int)> fill=[&](int used){
            if((used&full)==full){++transfer[entry][used>>m];return;}
            int first=0;while(used&(1<<first))++first;
            for(int piece:cover[first])if(!(used&piece))fill(used|piece);
        };
        fill(entry);
    }
    // Remove states that are unreachable from an empty boundary.
    vector<int> reachable{0};vector<bool> seen(states);seen[0]=true;
    for(int i=0;i<(int)reachable.size();++i)for(int j=0;j<states;++j)
        if(transfer[reachable[i]][j]&&!seen[j]){seen[j]=true;reachable.push_back(j);}
    int size=reachable.size();Matrix base(size,vector<long long>(size));
    for(int i=0;i<size;++i)for(int j=0;j<size;++j)base[i][j]=transfer[reachable[i]][reachable[j]]%MOD;
    vector<long long> row(size);row[0]=1;
    while(n){
        if(n&1){vector<long long> next(size);for(int i=0;i<size;++i)if(row[i])for(int j=0;j<size;++j)next[j]=(next[j]+row[i]*base[i][j])%MOD;row.swap(next);}
        n>>=1;if(n)base=product(base,base);
    }
    cout<<row[0]<<'\n';
}
