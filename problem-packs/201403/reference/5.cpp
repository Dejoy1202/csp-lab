#include <iostream>
#include <vector>
#include <array>
#include <algorithm>
using namespace std;
// For fixed choices let D be all dual-CPU time. They can run first.
// Remaining GPU jobs on CPU A run first; GPU jobs on B run last.
// CPU-only jobs fit in the complementary contiguous interval on each CPU.
// Thus the exact makespan is D + max(loadA, loadB, totalGPU).
// The DP includes D in all three loads and stores minimal third load.
int main() {
    int n; cin >> n;
    vector<array<int,4>> jobs(n);
    int upper=0;
    for(auto &job:jobs) { for(int &v:job) cin >> v; upper+=min(job[1],job[3]); }
    const int width=upper+1, INF=10000;
    vector<int> dp(width*width,INF); dp[0]=0;
    for (auto job : jobs) {
        int a=job[0], c=job[2], dual=min(job[1],job[3]);
        vector<int> next(width*width,INF);
        auto add=[&](int x,int y,int z) {
            if(x>upper||y>upper||z>upper) return;
            if(x>y) swap(x,y);
            int &slot=next[x*width+y]; slot=min(slot,z);
        };
        for(int x=0;x<=upper;++x) for(int y=x;y<=upper;++y) {
            int z=dp[x*width+y]; if(z==INF) continue;
            add(x+a,y,z); add(x,y+a,z);
            add(x+c,y,z+c); add(x,y+c,z+c);
            add(x+dual,y+dual,z+dual);
        }
        dp.swap(next);
    }
    int answer=upper;
    for(int x=0;x<=upper;++x) for(int y=x;y<=upper;++y)
        answer=min(answer,max({x,y,dp[x*width+y]}));
    cout << answer << '\n';
}
