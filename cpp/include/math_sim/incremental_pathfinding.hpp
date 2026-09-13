#pragma once

#include "math_sim/pathfinding_advanced.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <utility>
#include <vector>

namespace math_sim::incremental_pathfinding {

using Point = pathfinding_advanced::Point;
using SearchResult = pathfinding_advanced::SearchResult;

struct Key {
    double k1 = 0.0;
    double k2 = 0.0;
};

inline bool key_less(const Key& a, const Key& b) {
    if (a.k1 < b.k1 - 1e-12) return true;
    if (a.k1 > b.k1 + 1e-12) return false;
    return a.k2 < b.k2 - 1e-12;
}

struct QueueItem {
    Key key;
    int index = -1;
};

struct QueueCompare {
    bool operator()(const QueueItem& a, const QueueItem& b) const {
        return key_less(b.key, a.key);
    }
};

inline double static_enter_cost(const grid_advanced::GridMap& map, Point p) {
    return map.at(p.x,p.y).base_cost;
}

inline double min_cost(const grid_advanced::GridMap& map) {
    double m = std::numeric_limits<double>::infinity();
    for (const auto& c : map.cells) if (!c.blocked) m = std::min(m, c.base_cost);
    return std::isfinite(m) ? m : 0.0;
}

inline std::vector<Point> predecessors(const grid_advanced::GridMap& map, Point p, bool diagonal) {
    std::vector<Point> out;
    for (int y = std::max(0,p.y-1); y <= std::min(map.height-1,p.y+1); ++y) {
        for (int x = std::max(0,p.x-1); x <= std::min(map.width-1,p.x+1); ++x) {
            if (x==p.x && y==p.y) continue;
            Point q{x,y};
            for (const auto& nb : pathfinding_advanced::neighbors(map,q,diagonal)) {
                if (nb.point.x==p.x && nb.point.y==p.y) { out.push_back(q); break; }
            }
        }
    }
    return out;
}

class LPAStar {
public:
    LPAStar(grid_advanced::GridMap map, Point start, Point goal, bool diagonal=false)
        : map_(std::move(map)), start_(start), goal_(goal), diagonal_(diagonal),
          g_(static_cast<std::size_t>(map_.width*map_.height), inf()),
          rhs_(static_cast<std::size_t>(map_.width*map_.height), inf()) {
        const int s = map_.index(start_.x,start_.y);
        rhs_[static_cast<std::size_t>(s)] = 0.0;
        push(s);
    }

    const grid_advanced::GridMap& map() const { return map_; }
    std::size_t last_expansions() const { return last_expansions_; }

    void set_blocked(int x, int y, bool blocked) {
        if (!map_.in_bounds(x,y)) return;
        map_.at(x,y).blocked = blocked;
        update_around({x,y});
    }

    void set_cost(int x, int y, double cost) {
        if (!map_.in_bounds(x,y)) return;
        map_.at(x,y).base_cost = cost;
        update_around({x,y});
    }

    SearchResult compute() {
        last_expansions_ = 0;
        const int goal_i = map_.index(goal_.x,goal_.y);
        while (!open_.empty() && (key_less(open_.top().key, calculate_key(goal_i)) ||
               std::abs(rhs_[static_cast<std::size_t>(goal_i)] - g_[static_cast<std::size_t>(goal_i)]) > 1e-12)) {
            auto item = open_.top(); open_.pop();
            const Key current = calculate_key(item.index);
            if (key_less(item.key,current)) { open_.push({current,item.index}); continue; }
            ++last_expansions_;
            auto& gv = g_[static_cast<std::size_t>(item.index)];
            auto& rv = rhs_[static_cast<std::size_t>(item.index)];
            Point u{item.index % map_.width, item.index / map_.width};
            if (gv > rv) {
                gv = rv;
                for (const auto& nb : pathfinding_advanced::neighbors(map_,u,diagonal_)) update_vertex(map_.index(nb.point.x,nb.point.y));
            } else {
                gv = inf();
                update_vertex(item.index);
                for (const auto& nb : pathfinding_advanced::neighbors(map_,u,diagonal_)) update_vertex(map_.index(nb.point.x,nb.point.y));
            }
        }
        return build_result();
    }

private:
    static double inf() { return std::numeric_limits<double>::infinity(); }
    grid_advanced::GridMap map_;
    Point start_;
    Point goal_;
    bool diagonal_ = false;
    std::vector<double> g_, rhs_;
    std::priority_queue<QueueItem,std::vector<QueueItem>,QueueCompare> open_;
    std::size_t last_expansions_ = 0;

    Key calculate_key(int idx) const {
        Point p{idx % map_.width, idx / map_.width};
        const double m = std::min(g_[static_cast<std::size_t>(idx)], rhs_[static_cast<std::size_t>(idx)]);
        const double h = pathfinding_advanced::heuristic(p,goal_,diagonal_,min_cost(map_));
        return {m+h,m};
    }

    void push(int idx) { open_.push({calculate_key(idx),idx}); }

    void update_vertex(int idx) {
        const int s = map_.index(start_.x,start_.y);
        if (idx != s) {
            Point p{idx % map_.width, idx / map_.width};
            double best = inf();
            for (const auto& pred : predecessors(map_,p,diagonal_)) {
                const int pi = map_.index(pred.x,pred.y);
                if (map_.at(p.x,p.y).blocked) continue;
                best = std::min(best, g_[static_cast<std::size_t>(pi)] + static_enter_cost(map_,p));
            }
            rhs_[static_cast<std::size_t>(idx)] = best;
        }
        if (std::abs(g_[static_cast<std::size_t>(idx)] - rhs_[static_cast<std::size_t>(idx)]) > 1e-12) push(idx);
    }

    void update_around(Point p) {
        update_vertex(map_.index(p.x,p.y));
        for (const auto& nb : pathfinding_advanced::neighbors(map_,p,diagonal_)) update_vertex(map_.index(nb.point.x,nb.point.y));
        for (const auto& pred : predecessors(map_,p,diagonal_)) update_vertex(map_.index(pred.x,pred.y));
    }

    SearchResult build_result() const {
        SearchResult r; r.visited = last_expansions_;
        const int goal_i = map_.index(goal_.x,goal_.y);
        if (!std::isfinite(g_[static_cast<std::size_t>(goal_i)])) return r;
        r.found = true; r.cost = g_[static_cast<std::size_t>(goal_i)];
        Point cur = start_; r.path.push_back(cur);
        const int limit = map_.width*map_.height+1;
        for (int step=0; step<limit && !(cur.x==goal_.x && cur.y==goal_.y); ++step) {
            double best = inf(); Point bestp = cur;
            for (const auto& nb : pathfinding_advanced::neighbors(map_,cur,diagonal_)) {
                const int ni = map_.index(nb.point.x,nb.point.y);
                const double v = static_enter_cost(map_,nb.point) + g_[static_cast<std::size_t>(ni)];
                if (v < best) { best=v; bestp=nb.point; }
            }
            if (bestp.x==cur.x && bestp.y==cur.y) { r.found=false; r.path.clear(); r.cost=0.0; break; }
            cur = bestp; r.path.push_back(cur);
        }
        return r;
    }
};

class DStarLite {
public:
    DStarLite(grid_advanced::GridMap map, Point start, Point goal, bool diagonal=false)
        : planner_(std::move(map), goal, start, diagonal), start_(start), goal_(goal), diagonal_(diagonal) {}

    void set_blocked(int x,int y,bool blocked){ planner_.set_blocked(x,y,blocked); }
    void set_cost(int x,int y,double cost){ planner_.set_cost(x,y,cost); }
    std::size_t last_expansions() const { return planner_.last_expansions(); }
    const grid_advanced::GridMap& map() const { return planner_.map(); }

    SearchResult compute() {
        auto reverse = planner_.compute();
        SearchResult out; out.visited = reverse.visited; out.found = reverse.found; out.cost = reverse.cost;
        if (!reverse.found) return out;
        out.path.assign(reverse.path.rbegin(), reverse.path.rend());
        return out;
    }

private:
    LPAStar planner_;
    Point start_,goal_;
    bool diagonal_ = false;
};

} // namespace math_sim::incremental_pathfinding
