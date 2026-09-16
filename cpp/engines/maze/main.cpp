#include "math_sim/maze.hpp"
#include "math_sim/maze_generators.hpp"
#include "math_sim/maze_solvers.hpp"

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct Options {
    int width=24, height=18;
    std::uint64_t seed=42;
    std::string generator="backtracker";
    std::string solver="astar";
};
Options parse_args(int argc,char* argv[]){
    Options o;
    for(int i=1;i<argc;++i){std::string arg=argv[i]; auto value=[&](){if(i+1>=argc) throw std::invalid_argument("missing value for "+arg); return std::string(argv[++i]);};
        if(arg=="--width") o.width=std::stoi(value());
        else if(arg=="--height") o.height=std::stoi(value());
        else if(arg=="--seed") o.seed=std::stoull(value());
        else if(arg=="--generator") o.generator=value();
        else if(arg=="--solver") o.solver=value();
        else if(arg=="--help"){std::cout<<"Usage: maze [--width N] [--height N] [--seed N] [--generator backtracker|prim|kruskal|binary_tree|sidewinder|growing_tree|aldous_broder|wilson] [--solver bfs|bidirectional_bfs|dfs|astar|greedy|left_hand|right_hand|dead_end|random_mouse]\n"; std::exit(0);} else throw std::invalid_argument("unknown argument: "+arg);
    }
    if(o.width<2||o.height<2||o.width>120||o.height>90) throw std::invalid_argument("maze dimensions out of range");
    return o;
}
}

int main(int argc,char* argv[]){
    try{
        auto o=parse_args(argc,argv);
        std::vector<math_sim::maze_generators::CarveEdge> generation_trace;
        const auto generation_start=std::chrono::steady_clock::now();
        auto m=math_sim::maze_generators::generate(o.width,o.height,o.seed,o.generator,&generation_trace);
        const auto generation_end=std::chrono::steady_clock::now();
        const auto generation_us=std::chrono::duration_cast<std::chrono::microseconds>(generation_end-generation_start).count();

        std::size_t dead_ends=0, junctions=0, degree_sum=0;
        for(int y=0;y<m.height;++y){
            for(int x=0;x<m.width;++x){
                const auto degree=math_sim::maze::neighbors(m,{x,y}).size();
                degree_sum+=degree;
                if(degree==1) ++dead_ends;
                if(degree>=3) ++junctions;
            }
        }
        const double average_degree=m.cells.empty()?0.0:static_cast<double>(degree_sum)/static_cast<double>(m.cells.size());

        math_sim::maze::Point start{0,0}, goal{o.width-1,o.height-1};
        auto result=math_sim::maze_solvers::solve(m,start,goal,o.solver,o.seed);
        auto optimal=math_sim::maze_solvers::bfs(m,start,goal);
        std::cout<<std::setprecision(12)<<"{\"simulation\":\"maze\",\"width\":"<<m.width<<",\"height\":"<<m.height
                 <<",\"seed\":"<<o.seed<<",\"generator\":\""<<o.generator<<"\",\"solver\":\""<<o.solver<<"\",\"found\":"<<(result.found?"true":"false")
                 <<",\"visited\":"<<result.visited<<",\"optimal_steps\":"<<(optimal.path.empty()?0:optimal.path.size()-1)
                 <<",\"generation_us\":"<<generation_us<<",\"generation_steps\":"<<generation_trace.size()
                 <<",\"dead_ends\":"<<dead_ends<<",\"junctions\":"<<junctions<<",\"average_degree\":"<<average_degree
                 <<",\"walls\":[";
        for(std::size_t i=0;i<m.cells.size();++i){if(i) std::cout<<','; std::cout<<static_cast<int>(m.cells[i].walls);} std::cout<<"],\"path\":[";
        for(std::size_t i=0;i<result.path.size();++i){if(i) std::cout<<','; std::cout<<'['<<result.path[i].x<<','<<result.path[i].y<<']';}
        std::cout<<"],\"trace\":[";
        for(std::size_t i=0;i<result.trace.size();++i){if(i) std::cout<<','; std::cout<<'['<<result.trace[i].x<<','<<result.trace[i].y<<']';}
        std::cout<<"],\"generation_trace\":[";
        for(std::size_t i=0;i<generation_trace.size();++i){if(i) std::cout<<','; const auto& [a,b]=generation_trace[i]; std::cout<<'['<<a.x<<','<<a.y<<','<<b.x<<','<<b.y<<']';}
        std::cout<<"],\"optimal_path\":[";
        for(std::size_t i=0;i<optimal.path.size();++i){if(i) std::cout<<','; std::cout<<'['<<optimal.path[i].x<<','<<optimal.path[i].y<<']';}
        std::cout<<"]}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n'; return 1;}
}
