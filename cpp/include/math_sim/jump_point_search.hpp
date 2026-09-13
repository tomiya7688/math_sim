#pragma once

#include "math_sim/pathfinding_advanced.hpp"

#include <cmath>
#include <limits>
#include <queue>
#include <stdexcept>
#include <utility>
#include <vector>

namespace math_sim::jps {

using Point = pathfinding_advanced::Point;
using SearchResult = pathfinding_advanced::SearchResult;

inline bool walkable(const grid_advanced::GridMap& map, int x, int y) {
    return map.in_bounds(x, y) && !map.at(x, y).blocked;
}

inline bool uniform_static_grid(const grid_advanced::GridMap& map) {
    double value = -1.0;
    for (const auto& c : map.cells) {
        if (c.blocked) continue;
        if (c.dynamic_amplitude != 0.0 || c.exit_mask != grid_advanced::AllDirections) return false;
        if (value < 0.0) value = c.base_cost;
        else if (std::abs(c.base_cost - value) > 1e-12) return false;
    }
    return true;
}

inline bool forced(const grid_advanced::GridMap& map, int x, int y, int dx, int dy) {
    if (dx != 0 && dy != 0) {
        return (!walkable(map, x - dx, y) && walkable(map, x - dx, y + dy)) ||
               (!walkable(map, x, y - dy) && walkable(map, x + dx, y - dy));
    }
    if (dx != 0) {
        return (!walkable(map, x, y + 1) && walkable(map, x + dx, y + 1)) ||
               (!walkable(map, x, y - 1) && walkable(map, x + dx, y - 1));
    }
    return (!walkable(map, x + 1, y) && walkable(map, x + 1, y + dy)) ||
           (!walkable(map, x - 1, y) && walkable(map, x - 1, y + dy));
}

inline bool jump(const grid_advanced::GridMap& map, int x, int y, int dx, int dy, Point goal, Point& out) {
    const int nx = x + dx, ny = y + dy;
    if (!walkable(map, nx, ny)) return false;
    if (dx != 0 && dy != 0 && (!walkable(map, x + dx, y) || !walkable(map, x, y + dy))) return false;
    if (nx == goal.x && ny == goal.y) { out = {nx, ny}; return true; }
    if (forced(map, nx, ny, dx, dy)) { out = {nx, ny}; return true; }
    if (dx != 0 && dy != 0) {
        Point dummy;
        if (jump(map, nx, ny, dx, 0, goal, dummy) || jump(map, nx, ny, 0, dy, goal, dummy)) {
            out = {nx, ny}; return true;
        }
    }
    return jump(map, nx, ny, dx, dy, goal, out);
}

inline std::vector<std::pair<Point, double>> successors(const grid_advanced::GridMap& map, Point p, Point goal) {
    static constexpr int dirs[8][2] = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
    std::vector<std::pair<Point,double>> out;
    for (const auto& d : dirs) {
        Point jp;
        if (!jump(map, p.x, p.y, d[0], d[1], goal, jp)) continue;
        const double dx = static_cast<double>(std::abs(jp.x - p.x));
        const double dy = static_cast<double>(std::abs(jp.y - p.y));
        const double dist = std::max(dx, dy) + (1.4142135623730951 - 1.0) * std::min(dx, dy);
        out.push_back({jp, dist});
    }
    return out;
}

inline void append_segment(std::vector<Point>& path, Point a, Point b) {
    const int dx = (b.x > a.x) - (b.x < a.x);
    const int dy = (b.y > a.y) - (b.y < a.y);
    int x = a.x, y = a.y;
    while (x != b.x || y != b.y) {
        x += dx; y += dy;
        path.push_back({x,y});
    }
}

inline SearchResult search(const grid_advanced::GridMap& map, Point start, Point goal) {
    if (!uniform_static_grid(map)) throw std::invalid_argument("JPS requires a static uniform-cost grid without one-way restrictions");
    const int n = map.width * map.height;
    const int s = map.index(start.x,start.y), g = map.index(goal.x,goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> gs(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> closed(static_cast<std::size_t>(n), 0);
    using Item = std::pair<double,int>;
    std::priority_queue<Item,std::vector<Item>,std::greater<Item>> open;
    gs[static_cast<std::size_t>(s)] = 0.0;
    open.push({pathfinding_advanced::heuristic(start,goal,true,1.0),s});
    std::size_t visited = 0;
    while (!open.empty()) {
        const auto [_,idx] = open.top(); open.pop();
        if (closed[static_cast<std::size_t>(idx)]) continue;
        closed[static_cast<std::size_t>(idx)] = 1; ++visited;
        if (idx == g) break;
        Point p{idx % map.width, idx / map.width};
        for (const auto& [jp, step] : successors(map,p,goal)) {
            const int ji = map.index(jp.x,jp.y);
            const double ng = gs[static_cast<std::size_t>(idx)] + step;
            if (ng < gs[static_cast<std::size_t>(ji)]) {
                gs[static_cast<std::size_t>(ji)] = ng;
                parent[static_cast<std::size_t>(ji)] = idx;
                open.push({ng + pathfinding_advanced::heuristic(jp,goal,true,1.0), ji});
            }
        }
    }
    SearchResult r; r.visited = visited; r.found = std::isfinite(gs[static_cast<std::size_t>(g)]);
    if (!r.found) return r;
    std::vector<Point> jumps = pathfinding_advanced::reconstruct(map,parent,s,g);
    r.path.push_back(jumps.front());
    for (std::size_t i=1;i<jumps.size();++i) append_segment(r.path,jumps[i-1],jumps[i]);
    r.cost = gs[static_cast<std::size_t>(g)];
    return r;
}

} // namespace math_sim::jps
