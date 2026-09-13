#pragma once

#include "math_sim/maze.hpp"

#include <algorithm>
#include <cstddef>
#include <numeric>
#include <random>
#include <stack>
#include <string>
#include <tuple>
#include <vector>

namespace math_sim::maze_generators {

using maze::Maze;
using maze::Point;

inline std::vector<Point> raw_neighbors(const Maze& m, Point p) {
    std::vector<Point> out;
    if (m.in_bounds(p.x + 1, p.y)) out.push_back({p.x + 1, p.y});
    if (m.in_bounds(p.x - 1, p.y)) out.push_back({p.x - 1, p.y});
    if (m.in_bounds(p.x, p.y + 1)) out.push_back({p.x, p.y + 1});
    if (m.in_bounds(p.x, p.y - 1)) out.push_back({p.x, p.y - 1});
    return out;
}

inline Maze recursive_backtracker(int width, int height, std::uint64_t seed) {
    Maze m(width, height);
    std::mt19937_64 rng(seed);
    std::vector<char> seen(static_cast<std::size_t>(width * height), 0);
    std::stack<Point> st;
    st.push({0, 0}); seen[0] = 1;
    while (!st.empty()) {
        Point p = st.top();
        std::vector<Point> choices;
        for (auto n : raw_neighbors(m, p)) if (!seen[static_cast<std::size_t>(m.index(n.x, n.y))]) choices.push_back(n);
        if (choices.empty()) { st.pop(); continue; }
        std::uniform_int_distribution<std::size_t> pick(0, choices.size() - 1);
        Point n = choices[pick(rng)];
        maze::remove_wall(m, p, n);
        seen[static_cast<std::size_t>(m.index(n.x, n.y))] = 1;
        st.push(n);
    }
    return m;
}

inline Maze randomized_prim(int width, int height, std::uint64_t seed) {
    Maze m(width, height);
    std::mt19937_64 rng(seed);
    std::vector<char> in(static_cast<std::size_t>(width * height), 0);
    using Edge = std::pair<Point, Point>;
    std::vector<Edge> frontier;
    auto add = [&](Point p) {
        for (auto n : raw_neighbors(m, p)) if (!in[static_cast<std::size_t>(m.index(n.x, n.y))]) frontier.push_back({p, n});
    };
    in[0] = 1; add({0, 0});
    while (!frontier.empty()) {
        std::uniform_int_distribution<std::size_t> pick(0, frontier.size() - 1);
        const std::size_t i = pick(rng); auto [a, b] = frontier[i]; frontier[i] = frontier.back(); frontier.pop_back();
        if (in[static_cast<std::size_t>(m.index(b.x, b.y))]) continue;
        maze::remove_wall(m, a, b); in[static_cast<std::size_t>(m.index(b.x, b.y))] = 1; add(b);
    }
    return m;
}

struct DisjointSet {
    std::vector<int> p, r;
    explicit DisjointSet(int n) : p(static_cast<std::size_t>(n)), r(static_cast<std::size_t>(n), 0) { std::iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[static_cast<std::size_t>(x)] == x ? x : p[static_cast<std::size_t>(x)] = find(p[static_cast<std::size_t>(x)]); }
    bool unite(int a, int b) { a=find(a); b=find(b); if(a==b) return false; if(r[a]<r[b]) std::swap(a,b); p[b]=a; if(r[a]==r[b]) ++r[a]; return true; }
};

inline Maze randomized_kruskal(int width, int height, std::uint64_t seed) {
    Maze m(width, height); std::mt19937_64 rng(seed); DisjointSet ds(width * height);
    using Edge = std::pair<Point, Point>; std::vector<Edge> edges;
    for (int y=0;y<height;++y) for(int x=0;x<width;++x) { if(x+1<width) edges.push_back({{x,y},{x+1,y}}); if(y+1<height) edges.push_back({{x,y},{x,y+1}}); }
    std::shuffle(edges.begin(), edges.end(), rng);
    for (auto [a,b] : edges) if (ds.unite(m.index(a.x,a.y), m.index(b.x,b.y))) maze::remove_wall(m,a,b);
    return m;
}

inline Maze binary_tree(int width, int height, std::uint64_t seed) {
    Maze m(width,height); std::mt19937_64 rng(seed); std::bernoulli_distribution coin(0.5);
    for(int y=0;y<height;++y) for(int x=0;x<width;++x) {
        std::vector<Point> choices; if(x+1<width) choices.push_back({x+1,y}); if(y+1<height) choices.push_back({x,y+1});
        if(!choices.empty()) { Point n = choices.size()==1 ? choices[0] : choices[coin(rng)?1:0]; maze::remove_wall(m,{x,y},n); }
    }
    return m;
}

inline Maze sidewinder(int width, int height, std::uint64_t seed) {
    Maze m(width,height); std::mt19937_64 rng(seed); std::bernoulli_distribution close_run(0.5);
    for(int y=0;y<height;++y) {
        int run_start=0;
        for(int x=0;x<width;++x) {
            bool at_east = x == width-1; bool at_south = y == height-1;
            bool close = at_east || (!at_south && close_run(rng));
            if(close) {
                if(!at_south) { std::uniform_int_distribution<int> pick(run_start,x); int carve_x=pick(rng); maze::remove_wall(m,{carve_x,y},{carve_x,y+1}); }
                run_start=x+1;
            } else maze::remove_wall(m,{x,y},{x+1,y});
        }
    }
    return m;
}

inline Maze growing_tree(int width, int height, std::uint64_t seed, double newest_bias = 0.7) {
    Maze m(width,height); std::mt19937_64 rng(seed); std::vector<char> seen(static_cast<std::size_t>(width*height),0); std::vector<Point> active{{0,0}}; seen[0]=1; std::uniform_real_distribution<double> u(0.0,1.0);
    while(!active.empty()) {
        std::size_t idx;
        if(u(rng)<newest_bias) idx=active.size()-1; else { std::uniform_int_distribution<std::size_t> pick(0,active.size()-1); idx=pick(rng); }
        Point p=active[idx]; std::vector<Point> choices; for(auto n:raw_neighbors(m,p)) if(!seen[static_cast<std::size_t>(m.index(n.x,n.y))]) choices.push_back(n);
        if(choices.empty()) { active.erase(active.begin()+static_cast<std::ptrdiff_t>(idx)); continue; }
        std::uniform_int_distribution<std::size_t> pick(0,choices.size()-1); Point n=choices[pick(rng)]; maze::remove_wall(m,p,n); seen[static_cast<std::size_t>(m.index(n.x,n.y))]=1; active.push_back(n);
    }
    return m;
}

inline Maze aldous_broder(int width, int height, std::uint64_t seed) {
    Maze m(width, height); std::mt19937_64 rng(seed);
    const int total = width * height;
    std::uniform_int_distribution<int> start_pick(0, total - 1);
    int start_idx = start_pick(rng);
    Point current{start_idx % width, start_idx / width};
    std::vector<char> seen(static_cast<std::size_t>(total), 0);
    seen[static_cast<std::size_t>(start_idx)] = 1;
    int visited = 1;
    while (visited < total) {
        auto choices = raw_neighbors(m, current);
        std::uniform_int_distribution<std::size_t> pick(0, choices.size() - 1);
        Point next = choices[pick(rng)];
        int ni = m.index(next.x, next.y);
        if (!seen[static_cast<std::size_t>(ni)]) {
            maze::remove_wall(m, current, next);
            seen[static_cast<std::size_t>(ni)] = 1;
            ++visited;
        }
        current = next;
    }
    return m;
}

inline Maze wilson(int width, int height, std::uint64_t seed) {
    Maze m(width, height); std::mt19937_64 rng(seed);
    const int total = width * height;
    std::vector<char> in_tree(static_cast<std::size_t>(total), 0);
    std::uniform_int_distribution<int> root_pick(0, total - 1);
    in_tree[static_cast<std::size_t>(root_pick(rng))] = 1;
    int tree_count = 1;

    while (tree_count < total) {
        std::vector<int> unvisited;
        unvisited.reserve(static_cast<std::size_t>(total - tree_count));
        for (int i = 0; i < total; ++i) if (!in_tree[static_cast<std::size_t>(i)]) unvisited.push_back(i);
        std::uniform_int_distribution<std::size_t> start_pick(0, unvisited.size() - 1);
        int start_idx = unvisited[start_pick(rng)];
        Point current{start_idx % width, start_idx / width};
        std::vector<Point> walk{current};
        std::vector<int> position(static_cast<std::size_t>(total), -1);
        position[static_cast<std::size_t>(start_idx)] = 0;

        while (true) {
            auto choices = raw_neighbors(m, current);
            std::uniform_int_distribution<std::size_t> pick(0, choices.size() - 1);
            Point next = choices[pick(rng)];
            int ni = m.index(next.x, next.y);
            if (in_tree[static_cast<std::size_t>(ni)]) {
                walk.push_back(next);
                break;
            }
            int old_pos = position[static_cast<std::size_t>(ni)];
            if (old_pos >= 0) {
                for (std::size_t j = static_cast<std::size_t>(old_pos + 1); j < walk.size(); ++j) {
                    int old_idx = m.index(walk[j].x, walk[j].y);
                    position[static_cast<std::size_t>(old_idx)] = -1;
                }
                walk.resize(static_cast<std::size_t>(old_pos + 1));
            } else {
                position[static_cast<std::size_t>(ni)] = static_cast<int>(walk.size());
                walk.push_back(next);
            }
            current = next;
        }

        for (std::size_t i = 0; i + 1 < walk.size(); ++i) {
            maze::remove_wall(m, walk[i], walk[i + 1]);
            int idx = m.index(walk[i].x, walk[i].y);
            if (!in_tree[static_cast<std::size_t>(idx)]) {
                in_tree[static_cast<std::size_t>(idx)] = 1;
                ++tree_count;
            }
        }
    }
    return m;
}

inline Maze generate(int width, int height, std::uint64_t seed, const std::string& algorithm) {
    if (algorithm=="backtracker") return recursive_backtracker(width,height,seed);
    if (algorithm=="prim") return randomized_prim(width,height,seed);
    if (algorithm=="kruskal") return randomized_kruskal(width,height,seed);
    if (algorithm=="binary_tree") return binary_tree(width,height,seed);
    if (algorithm=="sidewinder") return sidewinder(width,height,seed);
    if (algorithm=="growing_tree") return growing_tree(width,height,seed);
    if (algorithm=="aldous_broder") return aldous_broder(width,height,seed);
    if (algorithm=="wilson") return wilson(width,height,seed);
    throw std::invalid_argument("unknown maze generator");
}

} // namespace math_sim::maze_generators
