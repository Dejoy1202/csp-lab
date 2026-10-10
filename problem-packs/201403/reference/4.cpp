#include <iostream>
#include <vector>
#include <queue>
#include <utility>
using namespace std;
int main() {
    int n, m, k; long long r; cin >> n >> m >> k >> r;
    int total = n + m;
    vector<pair<long long,long long>> point(total);
    for (auto &[x,y] : point) cin >> x >> y;
    vector<vector<int>> graph(total);
    for (int i=0;i<total;++i) for (int j=0;j<i;++j) {
        long long dx=point[i].first-point[j].first, dy=point[i].second-point[j].second;
        if (dx*dx+dy*dy <= r*r) { graph[i].push_back(j); graph[j].push_back(i); }
    }
    vector<vector<int>> distance(total,vector<int>(k+1,-1));
    queue<pair<int,int>> todo; todo.push({0,0}); distance[0][0]=0;
    while (!todo.empty()) {
        auto [u,used]=todo.front(); todo.pop();
        if (u==1) { cout << distance[u][used]-1 << '\n'; return 0; }
        for (int v : graph[u]) {
            int next=used+(v>=n);
            if (next<=k && distance[v][next]<0) {
                distance[v][next]=distance[u][used]+1; todo.push({v,next});
            }
        }
    }
}
