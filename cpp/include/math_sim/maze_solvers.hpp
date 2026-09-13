#pragma once

#include "math_sim/maze.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <stack>
#include <string>
#include <utility>
#include <vector>

namespace math_sim::maze_solvers {

using maze::Maze;
using maze::Point;

struct SolveResult {
    bool found = false;
    std::size_t visited = 0;
    std::vector<Point> path;
};

inline double manhattan(Point a, Point b) {
    return static_cast<double>(std::abs(a.x-b.x)+std::abs(a.y-b.y));
}

inline std::vector<Point> reconstruct(const Maze& m, const std::vector<int>& parent, int s, int g) {
    std::vector<Point> path;
    if(s!=g && parent[static_cast<std::size_t>(g)]<0) return path;
    for(int cur=g;;cur=parent[static_cast<std::size_t>(cur)]) {
        path.push_back({cur%m.width,cur/m.width});
        if(cur==s) break;
        if(cur<0) return {};
    }
    std::reverse(path.begin(),path.end());
    return path;
}

inline SolveResult bfs(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y);
    std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> seen(static_cast<std::size_t>(n),0); std::queue<int> q;
    q.push(s); seen[static_cast<std::size_t>(s)]=1; std::size_t visited=0;
    while(!q.empty()) { int idx=q.front(); q.pop(); ++visited; if(idx==g) break; Point p{idx%m.width,idx/m.width}; for(auto nb:maze::neighbors(m,p)){ int ni=m.index(nb.x,nb.y); if(seen[static_cast<std::size_t>(ni)]) continue; seen[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; q.push(ni);} }
    SolveResult r; r.visited=visited; r.found=seen[static_cast<std::size_t>(g)]!=0; if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult dfs(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y);
    std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> seen(static_cast<std::size_t>(n),0); std::stack<int> st;
    st.push(s); seen[static_cast<std::size_t>(s)]=1; std::size_t visited=0;
    while(!st.empty()) { int idx=st.top(); st.pop(); ++visited; if(idx==g) break; Point p{idx%m.width,idx/m.width}; auto ns=maze::neighbors(m,p); std::reverse(ns.begin(),ns.end()); for(auto nb:ns){ int ni=m.index(nb.x,nb.y); if(seen[static_cast<std::size_t>(ni)]) continue; seen[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; st.push(ni);} }
    SolveResult r; r.visited=visited; r.found=seen[static_cast<std::size_t>(g)]!=0; if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult a_star(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y); const double inf=std::numeric_limits<double>::infinity();
    std::vector<double> gs(static_cast<std::size_t>(n),inf); std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> closed(static_cast<std::size_t>(n),0);
    using Item=std::pair<double,int>; std::priority_queue<Item,std::vector<Item>,std::greater<Item>> open; gs[static_cast<std::size_t>(s)]=0; open.push({manhattan(start,goal),s}); std::size_t visited=0;
    while(!open.empty()){ auto [f,idx]=open.top(); open.pop(); (void)f; if(closed[static_cast<std::size_t>(idx)]) continue; closed[static_cast<std::size_t>(idx)]=1; ++visited; if(idx==g) break; Point p{idx%m.width,idx/m.width}; for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); double ng=gs[static_cast<std::size_t>(idx)]+1.0; if(ng<gs[static_cast<std::size_t>(ni)]){gs[static_cast<std::size_t>(ni)]=ng; parent[static_cast<std::size_t>(ni)]=idx; open.push({ng+manhattan(nb,goal),ni});}}}
    SolveResult r; r.visited=visited; r.found=std::isfinite(gs[static_cast<std::size_t>(g)]); if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult greedy(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y); std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> seen(static_cast<std::size_t>(n),0);
    using Item=std::pair<double,int>; std::priority_queue<Item,std::vector<Item>,std::greater<Item>> open; open.push({manhattan(start,goal),s}); seen[static_cast<std::size_t>(s)]=1; std::size_t visited=0;
    while(!open.empty()){auto [h,idx]=open.top(); open.pop(); (void)h; ++visited; if(idx==g) break; Point p{idx%m.width,idx/m.width}; for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); if(seen[static_cast<std::size_t>(ni)]) continue; seen[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; open.push({manhattan(nb,goal),ni});}}
    SolveResult r; r.visited=visited; r.found=seen[static_cast<std::size_t>(g)]!=0; if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult wall_follower(const Maze& m, Point start, Point goal, bool left_hand) {
    // Direction order: N,E,S,W. Start facing east.
    static const int dx[4]={0,1,0,-1}; static const int dy[4]={-1,0,1,0};
    Point p=start; int dir=1; std::vector<Point> path{p}; std::size_t visited=1;
    const std::size_t limit=static_cast<std::size_t>(m.width*m.height*16);
    for(std::size_t step=0; step<limit && !(p.x==goal.x&&p.y==goal.y); ++step) {
        int order[4];
        if(left_hand){order[0]=(dir+3)%4; order[1]=dir; order[2]=(dir+1)%4; order[3]=(dir+2)%4;}
        else {order[0]=(dir+1)%4; order[1]=dir; order[2]=(dir+3)%4; order[3]=(dir+2)%4;}
        bool moved=false;
        for(int k=0;k<4;++k){int nd=order[k]; if(maze::can_move(m,p,dx[nd],dy[nd])){p={p.x+dx[nd],p.y+dy[nd]}; dir=nd; path.push_back(p); ++visited; moved=true; break;}}
        if(!moved) break;
    }
    SolveResult r; r.visited=visited; r.found=(p.x==goal.x&&p.y==goal.y); if(r.found) r.path=std::move(path); return r;
}

inline SolveResult solve(const Maze& m, Point start, Point goal, const std::string& algorithm) {
    if(!m.in_bounds(start.x,start.y)||!m.in_bounds(goal.x,goal.y)) throw std::invalid_argument("start/goal out of bounds");
    if(algorithm=="bfs") return bfs(m,start,goal);
    if(algorithm=="dfs") return dfs(m,start,goal);
    if(algorithm=="astar") return a_star(m,start,goal);
    if(algorithm=="greedy") return greedy(m,start,goal);
    if(algorithm=="left_hand") return wall_follower(m,start,goal,true);
    if(algorithm=="right_hand") return wall_follower(m,start,goal,false);
    throw std::invalid_argument("unknown maze solver");
}

} // namespace math_sim::maze_solvers
