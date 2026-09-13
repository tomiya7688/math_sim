#pragma once

#include "math_sim/pathfinding.hpp"

#include <algorithm>
#include <cmath>
#include <deque>
#include <limits>
#include <queue>
#include <vector>

namespace math_sim::pathfinding::extra {

inline double min_step_cost(const grid::GridMap& map) {
    double value = std::numeric_limits<double>::infinity();
    for (const auto& cell : map.cells) {
        if (!cell.blocked) value = std::min(value, cell.cost);
    }
    return std::isfinite(value) ? value : 1.0;
}

inline SearchResult bellman_ford(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> dist(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    dist[static_cast<std::size_t>(s)] = 0.0;
    std::size_t visited = 0;

    for (int pass = 0; pass < n - 1; ++pass) {
        bool changed = false;
        for (int idx = 0; idx < n; ++idx) {
            if (!std::isfinite(dist[static_cast<std::size_t>(idx)])) continue;
            const Point p{idx % map.width, idx / map.width};
            if (map.at(p.x, p.y).blocked) continue;
            ++visited;
            for (const auto& nb : neighbors4(map, p)) {
                const int ni = map.index(nb.x, nb.y);
                const double nd = dist[static_cast<std::size_t>(idx)] + map.at(nb.x, nb.y).cost;
                if (nd < dist[static_cast<std::size_t>(ni)]) {
                    dist[static_cast<std::size_t>(ni)] = nd;
                    parent[static_cast<std::size_t>(ni)] = idx;
                    changed = true;
                }
            }
        }
        if (!changed) break;
    }

    SearchResult result;
    result.visited = visited;
    result.found = std::isfinite(dist[static_cast<std::size_t>(g)]);
    if (result.found) {
        result.cost = dist[static_cast<std::size_t>(g)];
        result.path = reconstruct(map, parent, s, g);
    }
    return result;
}

inline SearchResult spfa(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> dist(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> in_queue(static_cast<std::size_t>(n), 0);
    std::queue<int> q;
    dist[static_cast<std::size_t>(s)] = 0.0;
    q.push(s);
    in_queue[static_cast<std::size_t>(s)] = 1;
    std::size_t visited = 0;

    while (!q.empty()) {
        const int idx = q.front();
        q.pop();
        in_queue[static_cast<std::size_t>(idx)] = 0;
        ++visited;
        const Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors4(map, p)) {
            const int ni = map.index(nb.x, nb.y);
            const double nd = dist[static_cast<std::size_t>(idx)] + map.at(nb.x, nb.y).cost;
            if (nd < dist[static_cast<std::size_t>(ni)]) {
                dist[static_cast<std::size_t>(ni)] = nd;
                parent[static_cast<std::size_t>(ni)] = idx;
                if (!in_queue[static_cast<std::size_t>(ni)]) {
                    q.push(ni);
                    in_queue[static_cast<std::size_t>(ni)] = 1;
                }
            }
        }
    }

    SearchResult result;
    result.visited = visited;
    result.found = std::isfinite(dist[static_cast<std::size_t>(g)]);
    if (result.found) {
        result.cost = dist[static_cast<std::size_t>(g)];
        result.path = reconstruct(map, parent, s, g);
    }
    return result;
}

namespace detail {

inline bool depth_limited(
    const grid::GridMap& map,
    int current,
    int goal,
    int limit,
    int depth,
    std::vector<int>& parent,
    std::vector<char>& on_path,
    std::size_t& visited
) {
    ++visited;
    if (current == goal) return true;
    if (depth >= limit) return false;
    const Point p{current % map.width, current / map.width};
    for (const auto& nb : neighbors4(map, p)) {
        const int ni = map.index(nb.x, nb.y);
        if (on_path[static_cast<std::size_t>(ni)]) continue;
        on_path[static_cast<std::size_t>(ni)] = 1;
        parent[static_cast<std::size_t>(ni)] = current;
        if (depth_limited(map, ni, goal, limit, depth + 1, parent, on_path, visited)) return true;
        on_path[static_cast<std::size_t>(ni)] = 0;
        parent[static_cast<std::size_t>(ni)] = -1;
    }
    return false;
}

inline double ida_visit(
    const grid::GridMap& map,
    int current,
    int goal,
    double g_cost,
    double threshold,
    double min_step,
    std::vector<int>& parent,
    std::vector<char>& on_path,
    std::size_t& visited,
    bool& found
) {
    ++visited;
    const Point p{current % map.width, current / map.width};
    const Point goal_p{goal % map.width, goal / map.width};
    const double f = g_cost + manhattan(p, goal_p) * min_step;
    if (f > threshold) return f;
    if (current == goal) {
        found = true;
        return g_cost;
    }

    double next_threshold = std::numeric_limits<double>::infinity();
    for (const auto& nb : neighbors4(map, p)) {
        const int ni = map.index(nb.x, nb.y);
        if (on_path[static_cast<std::size_t>(ni)]) continue;
        on_path[static_cast<std::size_t>(ni)] = 1;
        parent[static_cast<std::size_t>(ni)] = current;
        const double t = ida_visit(
            map, ni, goal, g_cost + map.at(nb.x, nb.y).cost, threshold,
            min_step, parent, on_path, visited, found
        );
        if (found) return t;
        next_threshold = std::min(next_threshold, t);
        on_path[static_cast<std::size_t>(ni)] = 0;
        parent[static_cast<std::size_t>(ni)] = -1;
    }
    return next_threshold;
}

}  // namespace detail

inline SearchResult iterative_deepening_dfs(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    std::size_t visited = 0;

    for (int limit = 0; limit < n; ++limit) {
        std::vector<int> parent(static_cast<std::size_t>(n), -1);
        std::vector<char> on_path(static_cast<std::size_t>(n), 0);
        on_path[static_cast<std::size_t>(s)] = 1;
        if (detail::depth_limited(map, s, g, limit, 0, parent, on_path, visited)) {
            SearchResult result;
            result.found = true;
            result.visited = visited;
            result.path = reconstruct(map, parent, s, g);
            result.cost = path_cost(map, result.path);
            return result;
        }
    }
    return {false, 0.0, visited, {}};
}

inline SearchResult ida_star(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    const double min_step = min_step_cost(map);
    double threshold = manhattan(start, goal) * min_step;
    std::size_t visited = 0;

    while (std::isfinite(threshold)) {
        std::vector<int> parent(static_cast<std::size_t>(n), -1);
        std::vector<char> on_path(static_cast<std::size_t>(n), 0);
        on_path[static_cast<std::size_t>(s)] = 1;
        bool found = false;
        const double next = detail::ida_visit(
            map, s, g, 0.0, threshold, min_step, parent, on_path, visited, found
        );
        if (found) {
            SearchResult result;
            result.found = true;
            result.visited = visited;
            result.path = reconstruct(map, parent, s, g);
            result.cost = path_cost(map, result.path);
            return result;
        }
        if (!std::isfinite(next) || next <= threshold) break;
        threshold = next;
    }
    return {false, 0.0, visited, {}};
}

inline SearchResult fringe_search(const grid::GridMap& map, Point start, Point goal) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y);
    const int g = map.index(goal.x, goal.y);
    const double min_step = min_step_cost(map);
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> gscore(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<int> now{ s };
    std::vector<int> later;
    gscore[static_cast<std::size_t>(s)] = 0.0;
    double threshold = manhattan(start, goal) * min_step;
    std::size_t visited = 0;

    while (!now.empty()) {
        double next_threshold = inf;
        later.clear();
        std::vector<char> queued(static_cast<std::size_t>(n), 0);
        while (!now.empty()) {
            const int idx = now.back();
            now.pop_back();
            ++visited;
            const Point p{idx % map.width, idx / map.width};
            const double f = gscore[static_cast<std::size_t>(idx)] + manhattan(p, goal) * min_step;
            if (f > threshold) {
                next_threshold = std::min(next_threshold, f);
                if (!queued[static_cast<std::size_t>(idx)]) {
                    later.push_back(idx);
                    queued[static_cast<std::size_t>(idx)] = 1;
                }
                continue;
            }
            if (idx == g) {
                SearchResult result;
                result.found = true;
                result.visited = visited;
                result.path = reconstruct(map, parent, s, g);
                result.cost = path_cost(map, result.path);
                return result;
            }
            for (const auto& nb : neighbors4(map, p)) {
                const int ni = map.index(nb.x, nb.y);
                const double tentative = gscore[static_cast<std::size_t>(idx)] + map.at(nb.x, nb.y).cost;
                if (tentative < gscore[static_cast<std::size_t>(ni)]) {
                    gscore[static_cast<std::size_t>(ni)] = tentative;
                    parent[static_cast<std::size_t>(ni)] = idx;
                    now.push_back(ni);
                }
            }
        }
        if (!std::isfinite(next_threshold)) break;
        threshold = next_threshold;
        now.swap(later);
    }
    return {false, 0.0, visited, {}};
}

inline SearchResult solve(const grid::GridMap& map, Point start, Point goal, const std::string& algorithm) {
    if (algorithm == "bellman_ford") return bellman_ford(map, start, goal);
    if (algorithm == "spfa") return spfa(map, start, goal);
    if (algorithm == "iddfs") return iterative_deepening_dfs(map, start, goal);
    if (algorithm == "ida_star") return ida_star(map, start, goal);
    if (algorithm == "fringe") return fringe_search(map, start, goal);
    throw std::invalid_argument("unknown extra pathfinding algorithm");
}

}  // namespace math_sim::pathfinding::extra
