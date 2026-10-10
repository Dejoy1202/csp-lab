#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;
struct Rect { int x1, y1, x2, y2; };
int main() {
    int n, m; cin >> n >> m;
    vector<Rect> windows(n);
    vector<int> stack;
    for (int i = 0; i < n; ++i) {
        auto &w = windows[i]; cin >> w.x1 >> w.y1 >> w.x2 >> w.y2;
        stack.push_back(i);
    }
    while (m--) {
        int x, y, chosen = -1; cin >> x >> y;
        for (int j = n - 1; j >= 0; --j) {
            auto &w = windows[stack[j]];
            if (w.x1 <= x && x <= w.x2 && w.y1 <= y && y <= w.y2) {
                chosen = stack[j]; stack.erase(stack.begin() + j); stack.push_back(chosen); break;
            }
        }
        if (chosen < 0) cout << "IGNORED\n";
        else cout << chosen + 1 << '\n';
    }
}
