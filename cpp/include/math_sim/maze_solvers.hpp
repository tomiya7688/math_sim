#pragma once

#include "math_sim/maze.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>
#include <limits>
#include <queue>
#include <random>
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
    std::vector<Point> trace;
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
    q.push(s); seen[static_cast<std::size_t>(s)]=1; SolveResult r;
    while(!q.empty()) { int idx=q.front(); q.pop(); ++r.visited; Point p{idx%m.width,idx/m.width}; r.trace.push_back(p); if(idx==g) break; for(auto nb:maze::neighbors(m,p)){ int ni=m.index(nb.x,nb.y); if(seen[static_cast<std::size_t>(ni)]) continue; seen[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; q.push(ni);} }
    r.found=seen[static_cast<std::size_t>(g)]!=0; if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult bidirectional_bfs(const Maze& m, Point start, Point goal) {
    const int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y);
    SolveResult r;
    if(s==g) { r.found=true; r.visited=1; r.path={start}; r.trace={start}; return r; }
    std::vector<int> ps(static_cast<std::size_t>(n),-1), pg(static_cast<std::size_t>(n),-1);
    std::vector<char> ss(static_cast<std::size_t>(n),0), sg(static_cast<std::size_t>(n),0);
    std::queue<int> qs,qg; qs.push(s); qg.push(g); ss[s]=1; sg[g]=1; int meet=-1;
    auto expand=[&](std::queue<int>& q,std::vector<char>& own,const std::vector<char>& other,std::vector<int>& parent)->int{
        if(q.empty()) return -1; int idx=q.front(); q.pop(); ++r.visited; Point p{idx%m.width,idx/m.width}; r.trace.push_back(p);
        for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); if(own[static_cast<std::size_t>(ni)]) continue; own[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; if(other[static_cast<std::size_t>(ni)]) return ni; q.push(ni);} return -1;
    };
    while(!qs.empty()&&!qg.empty()&&meet<0){meet=qs.size()<=qg.size()?expand(qs,ss,sg,ps):expand(qg,sg,ss,pg);}
    r.found=meet>=0; if(!r.found) return r;
    auto left=reconstruct(m,ps,s,meet); std::vector<Point> right; for(int cur=meet;cur!=g;){cur=pg[static_cast<std::size_t>(cur)]; if(cur<0) return {}; right.push_back({cur%m.width,cur/m.width});}
    r.path=std::move(left); r.path.insert(r.path.end(),right.begin(),right.end()); return r;
}

inline SolveResult dfs(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y);
    std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> seen(static_cast<std::size_t>(n),0); std::stack<int> st;
    st.push(s); seen[static_cast<std::size_t>(s)]=1; SolveResult r;
    while(!st.empty()) { int idx=st.top(); st.pop(); ++r.visited; Point p{idx%m.width,idx/m.width}; r.trace.push_back(p); if(idx==g) break; auto ns=maze::neighbors(m,p); std::reverse(ns.begin(),ns.end()); for(auto nb:ns){ int ni=m.index(nb.x,nb.y); if(seen[static_cast<std::size_t>(ni)]) continue; seen[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; st.push(ni);} }
    r.found=seen[static_cast<std::size_t>(g)]!=0; if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult a_star(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y); const double inf=std::numeric_limits<double>::infinity();
    std::vector<double> gs(static_cast<std::size_t>(n),inf); std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> closed(static_cast<std::size_t>(n),0);
    using Item=std::pair<double,int>; std::priority_queue<Item,std::vector<Item>,std::greater<Item>> open; gs[static_cast<std::size_t>(s)]=0; open.push({manhattan(start,goal),s}); SolveResult r;
    while(!open.empty()){ auto [f,idx]=open.top(); open.pop(); (void)f; if(closed[static_cast<std::size_t>(idx)]) continue; closed[static_cast<std::size_t>(idx)]=1; ++r.visited; Point p{idx%m.width,idx/m.width}; r.trace.push_back(p); if(idx==g) break; for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); double ng=gs[static_cast<std::size_t>(idx)]+1.0; if(ng<gs[static_cast<std::size_t>(ni)]){gs[static_cast<std::size_t>(ni)]=ng; parent[static_cast<std::size_t>(ni)]=idx; open.push({ng+manhattan(nb,goal),ni});}}}
    r.found=std::isfinite(gs[static_cast<std::size_t>(g)]); if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult greedy(const Maze& m, Point start, Point goal) {
    int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y); std::vector<int> parent(static_cast<std::size_t>(n),-1); std::vector<char> seen(static_cast<std::size_t>(n),0);
    using Item=std::pair<double,int>; std::priority_queue<Item,std::vector<Item>,std::greater<Item>> open; open.push({manhattan(start,goal),s}); seen[static_cast<std::size_t>(s)]=1; SolveResult r;
    while(!open.empty()){auto [h,idx]=open.top(); open.pop(); (void)h; ++r.visited; Point p{idx%m.width,idx/m.width}; r.trace.push_back(p); if(idx==g) break; for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); if(seen[static_cast<std::size_t>(ni)]) continue; seen[static_cast<std::size_t>(ni)]=1; parent[static_cast<std::size_t>(ni)]=idx; open.push({manhattan(nb,goal),ni});}}
    r.found=seen[static_cast<std::size_t>(g)]!=0; if(r.found) r.path=reconstruct(m,parent,s,g); return r;
}

inline SolveResult wall_follower(const Maze& m, Point start, Point goal, bool left_hand) {
    static const int dx[4]={0,1,0,-1}; static const int dy[4]={-1,0,1,0};
    Point p=start; int dir=1; SolveResult r; r.trace.push_back(p); r.path.push_back(p); r.visited=1;
    const std::size_t limit=static_cast<std::size_t>(m.width*m.height*16);
    for(std::size_t step=0; step<limit && !(p.x==goal.x&&p.y==goal.y); ++step) {
        int order[4];
        if(left_hand){order[0]=(dir+3)%4; order[1]=dir; order[2]=(dir+1)%4; order[3]=(dir+2)%4;}
        else {order[0]=(dir+1)%4; order[1]=dir; order[2]=(dir+3)%4; order[3]=(dir+2)%4;}
        bool moved=false;
        for(int k=0;k<4;++k){int nd=order[k]; if(maze::can_move(m,p,dx[nd],dy[nd])){p={p.x+dx[nd],p.y+dy[nd]}; dir=nd; r.path.push_back(p); r.trace.push_back(p); ++r.visited; moved=true; break;}}
        if(!moved) break;
    }
    r.found=(p.x==goal.x&&p.y==goal.y); if(!r.found) r.path.clear(); return r;
}

inline SolveResult dead_end_filling(const Maze& m, Point start, Point goal) {
    const int n=m.width*m.height,s=m.index(start.x,start.y),g=m.index(goal.x,goal.y);
    std::vector<char> removed(static_cast<std::size_t>(n),0); std::queue<int> q; SolveResult r;
    auto degree=[&](int idx){Point p{idx%m.width,idx/m.width}; int d=0; for(auto nb:maze::neighbors(m,p)) if(!removed[static_cast<std::size_t>(m.index(nb.x,nb.y))]) ++d; return d;};
    for(int i=0;i<n;++i) if(i!=s&&i!=g&&degree(i)<=1) q.push(i);
    while(!q.empty()){int idx=q.front(); q.pop(); if(removed[static_cast<std::size_t>(idx)]||idx==s||idx==g||degree(idx)>1) continue; removed[static_cast<std::size_t>(idx)]=1; ++r.visited; r.trace.push_back({idx%m.width,idx/m.width}); Point p{idx%m.width,idx/m.width}; for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); if(ni!=s&&ni!=g&&!removed[static_cast<std::size_t>(ni)]&&degree(ni)<=1) q.push(ni);}}
    int cur=s,prev=-1; r.path.push_back(start); const std::size_t limit=static_cast<std::size_t>(n+1);
    for(std::size_t k=0;k<limit&&cur!=g;++k){Point p{cur%m.width,cur/m.width}; int next=-1; for(auto nb:maze::neighbors(m,p)){int ni=m.index(nb.x,nb.y); if(ni!=prev&&!removed[static_cast<std::size_t>(ni)]){next=ni; break;}} if(next<0) break; prev=cur; cur=next; r.path.push_back({cur%m.width,cur/m.width});}
    r.found=cur==g; if(!r.found) r.path.clear(); return r;
}

inline SolveResult random_mouse(const Maze& m, Point start, Point goal, std::uint64_t seed) {
    std::mt19937_64 rng(seed); Point p=start; SolveResult r; r.path.push_back(p); r.trace.push_back(p); r.visited=1;
    const std::size_t limit=static_cast<std::size_t>(m.width*m.height)*200;
    for(std::size_t i=0;i<limit&&!(p.x==goal.x&&p.y==goal.y);++i){auto ns=maze::neighbors(m,p); if(ns.empty()) break; std::uniform_int_distribution<std::size_t> pick(0,ns.size()-1); p=ns[pick(rng)]; r.path.push_back(p); r.trace.push_back(p); ++r.visited;}
    r.found=(p.x==goal.x&&p.y==goal.y); if(!r.found) r.path.clear(); return r;
}

inline SolveResult solve(const Maze& m, Point start, Point goal, const std::string& algorithm, std::uint64_t seed = 0) {
    if(!m.in_bounds(start.x,start.y)||!m.in_bounds(goal.x,goal.y)) throw std::invalid_argument("start/goal out of bounds");
    if(algorithm=="bfs") return bfs(m,start,goal);
    if(algorithm=="bidirectional_bfs") return bidirectional_bfs(m,start,goal);
    if(algorithm=="dfs") return dfs(m,start,goal);
    if(algorithm=="astar") return a_star(m,start,goal);
    if(algorithm=="greedy") return greedy(m,start,goal);
    if(algorithm=="left_hand") return wall_follower(m,start,goal,true);
    if(algorithm=="right_hand") return wall_follower(m,start,goal,false);
    if(algorithm=="dead_end") return dead_end_filling(m,start,goal);
    if(algorithm=="random_mouse") return random_mouse(m,start,goal,seed);
    throw std::invalid_argument("unknown maze solver");
}

} // namespace math_sim::maze_solvers
