#pragma once

#include "math_sim/grid_map_advanced.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <deque>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace math_sim::pathfinding_advanced {

struct Point { int x = 0; int y = 0; };

struct SearchOptions {
    bool diagonal = false;
    double start_time = 0.0;
    bool dynamic_costs = false;
};

struct SearchResult {
    bool found = false;
    double cost = 0.0;
    std::size_t visited = 0;
    std::vector<Point> path;
};

struct Neighbor {
    Point point;
    double distance_factor = 1.0;
};

inline std::vector<Neighbor> neighbors(const grid_advanced::GridMap& map, Point p, bool diagonal) {
    struct Move { int dx; int dy; std::uint8_t bit; double factor; };
    static constexpr Move moves8[] = {
        {1,0,grid_advanced::East,1.0}, {-1,0,grid_advanced::West,1.0},
        {0,1,grid_advanced::South,1.0}, {0,-1,grid_advanced::North,1.0},
        {1,1,grid_advanced::SouthEast,1.4142135623730951}, {-1,1,grid_advanced::SouthWest,1.4142135623730951},
        {1,-1,grid_advanced::NorthEast,1.4142135623730951}, {-1,-1,grid_advanced::NorthWest,1.4142135623730951},
    };
    const auto& from = map.at(p.x, p.y);
    std::vector<Neighbor> out;
    const int count = diagonal ? 8 : 4;
    out.reserve(static_cast<std::size_t>(count));
    for (int i = 0; i < count; ++i) {
        const auto& m = moves8[i];
        if ((from.exit_mask & m.bit) == 0) continue;
        const int nx = p.x + m.dx, ny = p.y + m.dy;
        if (!map.in_bounds(nx, ny) || map.at(nx, ny).blocked) continue;
        if (m.dx != 0 && m.dy != 0) {
            if (map.at(p.x + m.dx, p.y).blocked || map.at(p.x, p.y + m.dy).blocked) continue;
        }
        out.push_back({{nx, ny}, m.factor});
    }
    return out;
}

inline std::vector<Point> reconstruct(const grid_advanced::GridMap& map, const std::vector<int>& parent, int s, int g) {
    std::vector<Point> path;
    if (s != g && parent[static_cast<std::size_t>(g)] < 0) return path;
    for (int cur = g;; cur = parent[static_cast<std::size_t>(cur)]) {
        path.push_back({cur % map.width, cur / map.width});
        if (cur == s) break;
        if (cur < 0) return {};
    }
    std::reverse(path.begin(), path.end());
    return path;
}

inline double heuristic(Point a, Point b, bool diagonal, double min_step) {
    const double dx = std::abs(a.x - b.x), dy = std::abs(a.y - b.y);
    if (!diagonal) return (dx + dy) * min_step;
    const double mn = std::min(dx, dy), mx = std::max(dx, dy);
    return (mx - mn + 1.4142135623730951 * mn) * min_step;
}

inline double enter_cost(const grid_advanced::GridMap& map, const Neighbor& nb, double elapsed, const SearchOptions& options) {
    const auto& cell = map.at(nb.point.x, nb.point.y);
    const double c = options.dynamic_costs ? cell.cost_at(options.start_time + elapsed) : cell.base_cost;
    return c * nb.distance_factor;
}

inline SearchResult dijkstra(const grid_advanced::GridMap& map, Point start, Point goal, const SearchOptions& options = {}) {
    const int n = map.width * map.height;
    const int s = map.index(start.x, start.y), g = map.index(goal.x, goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    std::vector<double> dist(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> closed(static_cast<std::size_t>(n), 0);
    using Item = std::pair<double,int>;
    std::priority_queue<Item,std::vector<Item>,std::greater<Item>> pq;
    dist[static_cast<std::size_t>(s)] = 0.0; pq.push({0.0,s});
    std::size_t visited = 0;
    while (!pq.empty()) {
        const auto [d,idx] = pq.top(); pq.pop();
        if (closed[static_cast<std::size_t>(idx)]) continue;
        closed[static_cast<std::size_t>(idx)] = 1; ++visited;
        if (idx == g) break;
        Point p{idx % map.width, idx / map.width};
        for (const auto& nb : neighbors(map,p,options.diagonal)) {
            const int ni = map.index(nb.point.x, nb.point.y);
            const double nd = d + enter_cost(map, nb, d, options);
            if (nd < dist[static_cast<std::size_t>(ni)]) {
                dist[static_cast<std::size_t>(ni)] = nd; parent[static_cast<std::size_t>(ni)] = idx; pq.push({nd,ni});
            }
        }
    }
    SearchResult r; r.visited = visited; r.found = std::isfinite(dist[static_cast<std::size_t>(g)]);
    if (r.found) { r.cost = dist[static_cast<std::size_t>(g)]; r.path = reconstruct(map,parent,s,g); }
    return r;
}

inline SearchResult a_star(const grid_advanced::GridMap& map, Point start, Point goal, const SearchOptions& options = {}) {
    const int n = map.width * map.height;
    const int s = map.index(start.x,start.y), g = map.index(goal.x,goal.y);
    const double inf = std::numeric_limits<double>::infinity();
    double min_step = inf;
    for (const auto& c : map.cells) if (!c.blocked) min_step = std::min(min_step, c.base_cost);
    if (!std::isfinite(min_step)) min_step = 0.0;
    std::vector<double> gs(static_cast<std::size_t>(n), inf);
    std::vector<int> parent(static_cast<std::size_t>(n), -1);
    std::vector<char> closed(static_cast<std::size_t>(n), 0);
    using Item=std::pair<double,int>;
    std::priority_queue<Item,std::vector<Item>,std::greater<Item>> open;
    gs[static_cast<std::size_t>(s)] = 0.0; open.push({heuristic(start,goal,options.diagonal,min_step),s});
    std::size_t visited=0;
    while(!open.empty()) {
        const auto [f,idx]=open.top(); open.pop(); (void)f;
        if(closed[static_cast<std::size_t>(idx)]) continue;
        closed[static_cast<std::size_t>(idx)]=1; ++visited;
        if(idx==g) break;
        Point p{idx%map.width,idx/map.width};
        for(const auto& nb:neighbors(map,p,options.diagonal)) {
            const int ni=map.index(nb.point.x,nb.point.y);
            const double ng=gs[static_cast<std::size_t>(idx)] + enter_cost(map,nb,gs[static_cast<std::size_t>(idx)],options);
            if(ng<gs[static_cast<std::size_t>(ni)]) {
                gs[static_cast<std::size_t>(ni)]=ng; parent[static_cast<std::size_t>(ni)]=idx;
                open.push({ng+heuristic(nb.point,goal,options.diagonal,min_step),ni});
            }
        }
    }
    SearchResult r; r.visited=visited; r.found=std::isfinite(gs[static_cast<std::size_t>(g)]);
    if(r.found){r.cost=gs[static_cast<std::size_t>(g)]; r.path=reconstruct(map,parent,s,g);} return r;
}

inline SearchResult zero_one_bfs(const grid_advanced::GridMap& map, Point start, Point goal, const SearchOptions& options = {}) {
    if (options.diagonal) throw std::invalid_argument("0-1 BFS currently supports 4-way movement only");
    for (const auto& c : map.cells) if (!c.blocked && c.base_cost != 0.0 && c.base_cost != 1.0) throw std::invalid_argument("0-1 BFS requires costs 0 or 1");
    const int n=map.width*map.height, s=map.index(start.x,start.y), g=map.index(goal.x,goal.y);
    const int inf=std::numeric_limits<int>::max()/4;
    std::vector<int> dist(static_cast<std::size_t>(n),inf), parent(static_cast<std::size_t>(n),-1);
    std::deque<int> dq; dist[static_cast<std::size_t>(s)]=0; dq.push_front(s); std::size_t visited=0;
    while(!dq.empty()){
        const int idx=dq.front(); dq.pop_front(); ++visited; if(idx==g) break;
        Point p{idx%map.width,idx/map.width};
        for(const auto& nb:neighbors(map,p,false)){
            const int ni=map.index(nb.point.x,nb.point.y); const int w=static_cast<int>(map.at(nb.point.x,nb.point.y).base_cost);
            const int nd=dist[static_cast<std::size_t>(idx)]+w;
            if(nd<dist[static_cast<std::size_t>(ni)]){dist[static_cast<std::size_t>(ni)]=nd; parent[static_cast<std::size_t>(ni)]=idx; if(w==0)dq.push_front(ni);else dq.push_back(ni);} }
    }
    SearchResult r; r.visited=visited; r.found=dist[static_cast<std::size_t>(g)]<inf;
    if(r.found){r.cost=dist[static_cast<std::size_t>(g)]; r.path=reconstruct(map,parent,s,g);} return r;
}

inline SearchResult dial(const grid_advanced::GridMap& map, Point start, Point goal, int max_edge_cost, const SearchOptions& options = {}) {
    if (options.diagonal) throw std::invalid_argument("Dial currently supports 4-way movement only");
    if (max_edge_cost <= 0) throw std::invalid_argument("max_edge_cost must be positive");
    for (const auto& c : map.cells) if (!c.blocked && (c.base_cost < 0.0 || std::floor(c.base_cost) != c.base_cost || c.base_cost > max_edge_cost)) throw std::invalid_argument("Dial requires bounded non-negative integer costs");
    const int n=map.width*map.height, s=map.index(start.x,start.y), g=map.index(goal.x,goal.y);
    const int inf=std::numeric_limits<int>::max()/4;
    std::vector<int> dist(static_cast<std::size_t>(n),inf), parent(static_cast<std::size_t>(n),-1);
    const int max_distance=max_edge_cost*n;
    std::vector<std::vector<int>> buckets(static_cast<std::size_t>(max_distance+1));
    dist[static_cast<std::size_t>(s)]=0; buckets[0].push_back(s); std::size_t visited=0;
    for(int d=0; d<=max_distance; ++d){
        auto& bucket=buckets[static_cast<std::size_t>(d)];
        while(!bucket.empty()){
            const int idx=bucket.back(); bucket.pop_back(); if(dist[static_cast<std::size_t>(idx)]!=d) continue; ++visited; if(idx==g){SearchResult r{true,static_cast<double>(d),visited,reconstruct(map,parent,s,g)};return r;}
            Point p{idx%map.width,idx/map.width};
            for(const auto& nb:neighbors(map,p,false)){
                const int ni=map.index(nb.point.x,nb.point.y), w=static_cast<int>(map.at(nb.point.x,nb.point.y).base_cost), nd=d+w;
                if(nd<dist[static_cast<std::size_t>(ni)] && nd<=max_distance){dist[static_cast<std::size_t>(ni)]=nd; parent[static_cast<std::size_t>(ni)]=idx; buckets[static_cast<std::size_t>(nd)].push_back(ni);} }
        }
    }
    SearchResult r; r.visited=visited; return r;
}

inline SearchResult solve(const grid_advanced::GridMap& map, Point start, Point goal, const std::string& algorithm, const SearchOptions& options = {}, int max_edge_cost = 9) {
    if (!map.in_bounds(start.x,start.y) || !map.in_bounds(goal.x,goal.y)) throw std::invalid_argument("start/goal out of bounds");
    if (map.at(start.x,start.y).blocked || map.at(goal.x,goal.y).blocked) throw std::invalid_argument("start/goal cannot be blocked");
    if (algorithm=="dijkstra") return dijkstra(map,start,goal,options);
    if (algorithm=="astar") return a_star(map,start,goal,options);
    if (algorithm=="zero_one_bfs") return zero_one_bfs(map,start,goal,options);
    if (algorithm=="dial") return dial(map,start,goal,max_edge_cost,options);
    throw std::invalid_argument("unknown advanced algorithm");
}

} // namespace math_sim::pathfinding_advanced
