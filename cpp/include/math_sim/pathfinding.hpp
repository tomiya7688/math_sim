#pragma once

#include "math_sim/grid_map.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
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

inline SearchResult a_star(const grid::GridMap& map, Point start, Point goal) {
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
    open.push({manhattan(start, goal) * min_step, s});
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
                const double f = tentative + manhattan(nb, goal) * min_step;
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
        result.cost = result.path.size() > 1 ? static_cast<double>(result.path.size() - 1) : 0.0;
    }
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
        double total = 0.0;
        for (std::size_t i = 1; i < result.path.size(); ++i) total += map.at(result.path[i].x, result.path[i].y).cost;
        result.cost = total;
    }
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
    if (algorithm == "astar") return a_star(map, start, goal);
    if (algorithm == "bfs") return bfs(map, start, goal);
    if (algorithm == "greedy") return greedy_best_first(map, start, goal);
    throw std::invalid_argument("unknown algorithm");
}

}  // namespace math_sim::pathfinding
