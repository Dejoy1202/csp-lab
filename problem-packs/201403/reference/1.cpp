#include <iostream>
#include <set>
using namespace std;
int main() {
    int n, x, answer = 0;
    cin >> n;
    set<int> present;
    for (int i = 0; i < n; ++i) { cin >> x; present.insert(x); }
    for (int x : present) if (x > 0 && present.count(-x)) ++answer;
    cout << answer << '\n';
}
