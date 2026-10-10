#include <iostream>
#include <sstream>
#include <map>
#include <string>
using namespace std;
int main() {
    string format; int n; cin >> format >> n;
    map<char, bool> accepts;
    for (int i = 0; i < (int)format.size(); ++i) {
        if (format[i] == ':') continue;
        accepts[format[i]] = i + 1 < (int)format.size() && format[i+1] == ':';
    }
    string line; getline(cin, line);
    for (int row = 1; row <= n; ++row) {
        getline(cin, line); istringstream words(line); string word, argument;
        words >> word;
        map<char, string> found;
        while (words >> word) {
            if (word.size() != 2 || word[0] != '-' || !accepts.count(word[1])) break;
            argument.clear();
            if (accepts[word[1]] && !(words >> argument)) break;
            found[word[1]] = argument;
        }
        cout << "Case " << row << ':';
        for (const auto &[option, value] : found) {
            cout << " -" << option;
            if (accepts[option]) cout << ' ' << value;
        }
        cout << '\n';
    }
}
