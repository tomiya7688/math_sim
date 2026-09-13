#include "math_sim/maze.hpp"
#include "math_sim/maze_generators.hpp"
#include "math_sim/maze_solvers.hpp"

#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

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
        auto m=math_sim::maze_generators::generate(o.width,o.height,o.seed,o.generator);
        math_sim::maze::Point start{0,0}, goal{o.width-1,o.height-1};
        auto result=math_sim::maze_solvers::solve(m,start,goal,o.solver,o.seed);
        auto optimal=math_sim::maze_solvers::bfs(m,start,goal);
        std::cout<<std::setprecision(12)<<"{\"simulation\":\"maze\",\"width\":"<<m.width<<",\"height\":"<<m.height
                 <<",\"seed\":"<<o.seed<<",\"generator\":\""<<o.generator<<"\",\"solver\":\""<<o.solver<<"\",\"found\":"<<(result.found?"true":"false")
                 <<",\"visited\":"<<result.visited<<",\"optimal_steps\":"<<(optimal.path.empty()?0:optimal.path.size()-1)<<",\"walls\":[";
        for(std::size_t i=0;i<m.cells.size();++i){if(i) std::cout<<','; std::cout<<static_cast<int>(m.cells[i].walls);} std::cout<<"],\"path\":[";
        for(std::size_t i=0;i<result.path.size();++i){if(i) std::cout<<','; std::cout<<'['<<result.path[i].x<<','<<result.path[i].y<<']';}
        std::cout<<"],\"optimal_path\":[";
        for(std::size_t i=0;i<optimal.path.size();++i){if(i) std::cout<<','; std::cout<<'['<<optimal.path[i].x<<','<<optimal.path[i].y<<']';}
        std::cout<<"]}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n'; return 1;}
}
