#pragma once

#include "math_sim/grid_map.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <stack>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace math_sim::pathfinding {

struct Point {
    int x = 0;
    int y = 0;
};

struct SearchResult {
    bool found = false;
    double cost = 0.0;
    std::size_t visited = 0;
    std::vector<Point> path;
};

inline double manhattan(const Point& a, const Point& b) {
    return static_cast<double>(std::abs(a.x - b.x) + std::abs(a.y - b.y));
}

inline std::vector<Point> neighbors4(const grid::GridMap& map, const Point& p) {
    static constexpr int dx[4] = {1, -1, 0, 0};
    static constexpr int dy[4] = {0, 0, 1, -1};
    std::vector<Point> out;
    out.reserve(4);
    for (int i = 0; i < 4; ++i) {
        const int nx = p.x + dx[i];
        const int ny = p.y + dy[i];
        if (map.in_bounds(nx, ny) && !map.at(nx, ny).blocked) out.push_back({nx, ny});
    }
    return out;
}

inline std::vector<Point> reconstruct(
    const grid::GridMap& map,
    const std::vector<int>& parent,
    int start_index,
    int goal_index
) {
    std::vector<Point> path;
    if (start_index != goal_index && parent[static_cast<std::size_t>(goal_index)] < 0) return path;
    for (int cur = goal_index;; cur = parent[static_cast<std::size_t>(cur)]) {
        path.push_back({cur % map.width, cur / map.width});
        if (cur == start_index) break;
        if (cur < 0) return {};
    }
    std::reverse(path.begin(), path.end());
    return path;
}

inline double path_cost(const grid::GridMap& map, const std::vector<Point>& path) {
    double total = 0.0;
    for (std::size_t i = 1; i < path.size(); ++i) {
        total += map.at(path[i].x, path[i].y).cost;
    }
    return total;
}

inline SearchResult dijkstra(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> dist(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> closed(static_cast<std::size_t>(n), 0);
    using Item = std::pair<double, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> pq;
    dist[static_cast<std::size_t>(s)] = 0.0;
    pq.push({0.0, s});
    std::size_t visited = 0;

    while (!pq.empty()) {
        const auto [d, idx] = pq.top(); pq.pop();
        if (closed[static_cast<std::size_t>(idx)]) continue;
        closed[static_cast<std::size_t>(idx)] = 1;
        ++visited;
        if (idx == g) break;
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            const double nd = d + map.at(nb.x, nb.y).cost;
            if (nd < dist[static_cast<std::size_t>(ni)]) {
                dist[static_cast<std::size_t>(ni)] = nd;
                parent[static_cast<std::size_t>(ni)] = idx;
                pq.push({nd, ni});
            }
        }
    }

    SearchResult result;
    result.visited = visited;
    result.found = std::isfinite(dist[static_cast<std::size_t>(g)]);
    result.cost = result.found ? dist[static_cast<std::size_t>(g)] : 0.0;
    if (result.found) result.path = reconstruct(map, parent, s, g);
    return result;
}

inline SearchResult weighted_a_star(
    const grid::GridMap& map,
    Point start,
    Point goal,
    double heuristic_weight = 1.5
) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    double min_step = inf;
    for (const auto& c : map.cells) if (!c.blocked) min_step = std::min(min_step, c.cost);
    if (!std::isfinite(min_step)) min_step = 1.0;
    std::vector<double> gscore(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> closed(static_cast<std::size_t>(n), 0);
    using Item = std::pair<double, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> open;
    gscore[static_cast<std::size_t>(s)] = 0.0;
    open.push({heuristic_weight * manhattan(start, goal) * min_step, s});
    std::size_t visited = 0;

    while (!open.empty()) {
        const auto [_, idx] = open.top(); open.pop();
        if (closed[static_cast<std::size_t>(idx)]) continue;
        closed[static_cast<std::size_t>(idx)] = 1;
        ++visited;
        if (idx == g) break;
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            const double tentative = gscore[static_cast<std::size_t>(idx)] + map.at(nb.x, nb.y).cost;
            if (tentative < gscore[static_cast<std::size_t>(ni)]) {
                gscore[static_cast<std::size_t>(ni)] = tentative;
                parent[static_cast<std::size_t>(ni)] = idx;
                const double f = tentative + heuristic_weight * manhattan(nb, goal) * min_step;
                open.push({f, ni});
            }
        }
    }

    SearchResult result;
    result.visited = visited;
    result.found = std::isfinite(gscore[static_cast<std::size_t>(g)]);
    result.cost = result.found ? gscore[static_cast<std::size_t>(g)] : 0.0;
    if (result.found) result.path = reconstruct(map, parent, s, g);
    return result;
}

inline SearchResult a_star(const grid::GridMap& map, Point start, Point goal) {
    return weighted_a_star(map, start, goal, 1.0);
}

inline SearchResult bfs(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> seen(static_cast<std::size_t>(n), 0);
    std::queue<int> q;
    q.push(s); seen[static_cast<std::size_t>(s)] = 1;
    std::size_t visited = 0;
    while (!q.empty()) {
        const int idx = q.front(); q.pop(); ++visited;
        if (idx == g) break;
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            if (seen[static_cast<std::size_t>(ni)]) continue;
            seen[static_cast<std::size_t>(ni)] = 1;
            parent[static_cast<std::size_t>(ni)] = idx;
            q.push(ni);
        }
    }
    SearchResult result;
    result.visited = visited;
    result.found = seen[static_cast<std::size_t>(g)] != 0;
    if (result.found) {
        result.path = reconstruct(map, parent, s, g);
        result.cost = static_cast<double>(result.path.size() > 1 ? result.path.size() - 1 : 0);
    }
    return result;
}

inline SearchResult dfs(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> seen(static_cast<std::size_t>(n), 0);
    std::stack<int> st;
    st.push(s);
    seen[static_cast<std::size_t>(s)] = 1;
    std::size_t visited = 0;
    while (!st.empty()) {
        const int idx = st.top(); st.pop(); ++visited;
        if (idx == g) break;
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            if (seen[static_cast<std::size_t>(ni)]) continue;
            seen[static_cast<std::size_t>(ni)] = 1;
            parent[static_cast<std::size_t>(ni)] = idx;
            st.push(ni);
        }
    }
    SearchResult result;
    result.visited = visited;
    result.found = seen[static_cast<std::size_t>(g)] != 0;
    if (result.found) {
        result.path = reconstruct(map, parent, s, g);
        result.cost = path_cost(map, result.path);
    }
    return result;
}

inline SearchResult bidirectional_bfs(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    if (s == g) return {true, 0.0, 1, {start}};

    std::vector<int> parent_s(static_cast<std::size_t>(n), -1);
    std::vector<int> parent_g(static_cast<std::size_t>(n), -1);
    std::vector<char> seen_s(static_cast<std::size_t>(n), 0);
    std::vector<char> seen_g(static_cast<std::size_t>(n), 0);
    std::queue<int> qs, qg;
    qs.push(s); qg.push(g);
    seen_s[static_cast<std::size_t>(s)] = 1;
    seen_g[static_cast<std::size_t>(g)] = 1;
    int meet = -1;
    std::size_t visited = 0;

    auto expand = [&](std::queue<int>& q, std::vector<char>& own, std::vector<char>& other,
                      std::vector<int>& parent) -> int {
        const std::size_t layer = q.size();
        for (std::size_t k = 0; k < layer; ++k) {
            const int idx = q.front(); q.pop(); ++visited;
            const Point p{idx % map.width, idx / map.width};
            for (const auto& nb : neighbors4(map, p)) {
                const int ni = map.index(nb.x, nb.y);
                if (own[static_cast<std::size_t>(ni)]) continue;
                own[static_cast<std::size_t>(ni)] = 1;
                parent[static_cast<std::size_t>(ni)] = idx;
                if (other[static_cast<std::size_t>(ni)]) return ni;
                q.push(ni);
            }
        }
        return -1;
    };

    while (!qs.empty() && !qg.empty() && meet < 0) {
        meet = expand(qs, seen_s, seen_g, parent_s);
        if (meet >= 0) break;
        meet = expand(qg, seen_g, seen_s, parent_g);
    }

    SearchResult result;
    result.visited = visited;
    result.found = meet >= 0;
    if (!result.found) return result;

    auto left = reconstruct(map, parent_s, s, meet);
    std::vector<Point> right;
    for (int cur = meet; cur != g;) {
        cur = parent_g[static_cast<std::size_t>(cur)];
        if (cur < 0) return {};
        right.push_back({cur % map.width, cur / map.width});
    }
    result.path = std::move(left);
    result.path.insert(result.path.end(), right.begin(), right.end());
    result.cost = static_cast<double>(result.path.size() > 1 ? result.path.size() - 1 : 0);
    return result;
}

inline SearchResult greedy_best_first(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> seen(static_cast<std::size_t>(n), 0);
    using Item = std::pair<double, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> open;
    open.push({manhattan(start, goal), s});
    seen[static_cast<std::size_t>(s)] = 1;
    std::size_t visited = 0;
    while (!open.empty()) {
        const auto [_, idx] = open.top(); open.pop(); ++visited;
        if (idx == g) break;
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            if (seen[static_cast<std::size_t>(ni)]) continue;
            seen[static_cast<std::size_t>(ni)] = 1;
            parent[static_cast<std::size_t>(ni)] = idx;
            open.push({manhattan(nb, goal), ni});
        }
    }
    SearchResult result;
    result.visited = visited;
    result.found = seen[static_cast<std::size_t>(g)] != 0;
    if (result.found) {
        result.path = reconstruct(map, parent, s, g);
        result.cost = path_cost(map, result.path);
    }
    return result;
}

inline SearchResult bidirectional_dijkstra(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    if (s == g) return {true, 0.0, 1, {start}};
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> ds(static_cast<std::size_t>(n), inf), dg(static_cast<std::size_t>(n), inf);
    std::vector<int> ps(static_cast<std::size_t>(n), -1), pg(static_cast<std::size_t>(n), -1);
    std::vector<char> cs(static_cast<std::size_t>(n), 0), cg(static_cast<std::size_t>(n), 0);
    using Item = std::pair<double, int>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> qs, qg;
    ds[static_cast<std::size_t>(s)] = 0.0;
    dg[static_cast<std::size_t>(g)] = 0.0;
    qs.push({0.0, s}); qg.push({0.0, g});
    double best = inf;
    int meet = -1;
    std::size_t visited = 0;

    auto relax_forward = [&]() {
        while (!qs.empty() && cs[static_cast<std::size_t>(qs.top().second)]) qs.pop();
        if (qs.empty()) return;
        const auto [d, idx] = qs.top(); qs.pop();
        cs[static_cast<std::size_t>(idx)] = 1; ++visited;
        if (cg[static_cast<std::size_t>(idx)] && d + dg[static_cast<std::size_t>(idx)] < best) {
            best = d + dg[static_cast<std::size_t>(idx)]; meet = idx;
        }
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            const double nd = d + map.at(nb.x, nb.y).cost;
            if (nd < ds[static_cast<std::size_t>(ni)]) {
                ds[static_cast<std::size_t>(ni)] = nd; ps[static_cast<std::size_t>(ni)] = idx; qs.push({nd, ni});
            }
            if (std::isfinite(dg[static_cast<std::size_t>(ni)]) && nd + dg[static_cast<std::size_t>(ni)] < best) {
                best = nd + dg[static_cast<std::size_t>(ni)]; meet = ni;
            }
        }
    };

    auto relax_backward = [&]() {
        while (!qg.empty() && cg[static_cast<std::size_t>(qg.top().second)]) qg.pop();
        if (qg.empty()) return;
        const auto [d, idx] = qg.top(); qg.pop();
        cg[static_cast<std::size_t>(idx)] = 1; ++visited;
        if (cs[static_cast<std::size_t>(idx)] && d + ds[static_cast<std::size_t>(idx)] < best) {
            best = d + ds[static_cast<std::size_t>(idx)]; meet = idx;
        }
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            const double nd = d + map.at(p.x, p.y).cost;
            if (nd < dg[static_cast<std::size_t>(ni)]) {
                dg[static_cast<std::size_t>(ni)] = nd; pg[static_cast<std::size_t>(ni)] = idx; qg.push({nd, ni});
            }
            if (std::isfinite(ds[static_cast<std::size_t>(ni)]) && nd + ds[static_cast<std::size_t>(ni)] < best) {
                best = nd + ds[static_cast<std::size_t>(ni)]; meet = ni;
            }
        }
    };

    while (!qs.empty() && !qg.empty()) {
        const double fs = qs.empty() ? inf : qs.top().first;
        const double fg = qg.empty() ? inf : qg.top().first;
        if (fs + fg >= best) break;
        if (fs <= fg) relax_forward(); else relax_backward();
    }

    SearchResult result;
    result.visited = visited;
    result.found = meet >= 0;
    if (!result.found) return result;
    auto left = reconstruct(map, ps, s, meet);
    std::vector<Point> right;
    for (int cur = meet; cur != g;) {
        cur = pg[static_cast<std::size_t>(cur)];
        if (cur < 0) return {};
        right.push_back({cur % map.width, cur / map.width});
    }
    result.path = std::move(left);
    result.path.insert(result.path.end(), right.begin(), right.end());
    result.cost = path_cost(map, result.path);
    return result;
}

inline SearchResult solve(const grid::GridMap& map, Point start, Point goal, const std::string& algorithm) {
    if (!map.in_bounds(start.x, start.y) || !map.in_bounds(goal.x, goal.y)) {
        throw std::invalid_argument("start/goal out of bounds");
    }
    if (map.at(start.x, start.y).blocked || map.at(goal.x, goal.y).blocked) {
        throw std::invalid_argument("start/goal cannot be blocked");
    }
    if (algorithm == "dijkstra") return dijkstra(map, start, goal);
    if (algorithm == "bidijkstra") return bidirectional_dijkstra(map, start, goal);
    if (algorithm == "astar") return a_star(map, start, goal);
    if (algorithm == "weighted_astar") return weighted_a_star(map, start, goal, 1.5);
    if (algorithm == "bfs") return bfs(map, start, goal);
    if (algorithm == "bibfs") return bidirectional_bfs(map, start, goal);
    if (algorithm == "dfs") return dfs(map, start, goal);
    if (algorithm == "greedy") return greedy_best_first(map, start, goal);
    throw std::invalid_argument("unknown algorithm");
}

}  // namespace math_sim::pathfinding
