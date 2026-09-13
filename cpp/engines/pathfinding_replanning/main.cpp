#include "math_sim/grid_map_advanced.hpp"
#include "math_sim/incremental_pathfinding.hpp"
#include "math_sim/pathfinding_advanced.hpp"

#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

struct Options {
    int width = 32;
    int height = 24;
    double obstacles = 0.15;
    std::uint64_t seed = 42;
    std::string algorithm = "lpa_star";
    bool diagonal = false;
    int block_x = -1;
    int block_y = -1;
};

Options parse_args(int argc, char* argv[]) {
    Options o;
    for (int i=1;i<argc;++i) {
        const std::string arg = argv[i];
        auto value = [&]() -> std::string {
            if (i+1>=argc) throw std::invalid_argument("missing value for " + arg);
            return argv[++i];
        };
        if (arg=="--width") o.width=std::stoi(value());
        else if (arg=="--height") o.height=std::stoi(value());
        else if (arg=="--obstacles") o.obstacles=std::stod(value());
        else if (arg=="--seed") o.seed=std::stoull(value());
        else if (arg=="--algorithm") o.algorithm=value();
        else if (arg=="--diagonal") o.diagonal=std::stoi(value())!=0;
        else if (arg=="--block-x") o.block_x=std::stoi(value());
        else if (arg=="--block-y") o.block_y=std::stoi(value());
        else throw std::invalid_argument("unknown argument: " + arg);
    }
    if (o.algorithm!="lpa_star" && o.algorithm!="dstar_lite") throw std::invalid_argument("algorithm must be lpa_star or dstar_lite");
    if (o.width < 2 || o.height < 2) throw std::invalid_argument("grid dimensions must be at least 2");
    if (o.obstacles < 0.0 || o.obstacles >= 1.0) throw std::invalid_argument("obstacles must be in [0,1)");
    return o;
}

template <typename Planner>
void run(Planner& planner, const math_sim::grid_advanced::GridMap& original_map, const Options& options) {
    auto first = planner.compute();
    bool changed = false;
    int changed_x = options.block_x, changed_y = options.block_y;

    if (changed_x < 0 || changed_y < 0) {
        if (first.path.size() > 2) {
            const auto p = first.path[first.path.size()/2];
            changed_x = p.x;
            changed_y = p.y;
        }
    }

    if (changed_x >= 0 && changed_y >= 0 &&
        changed_x < original_map.width && changed_y < original_map.height &&
        !(changed_x == 0 && changed_y == 0) &&
        !(changed_x == original_map.width - 1 && changed_y == original_map.height - 1)) {
        planner.set_blocked(changed_x, changed_y, true);
        changed = true;
    }

    auto second = planner.compute();

    std::cout << std::setprecision(12)
              << "{\"simulation\":\"pathfinding_replanning\","
              << "\"algorithm\":\"" << options.algorithm << "\","
              << "\"width\":" << original_map.width << ','
              << "\"height\":" << original_map.height << ','
              << "\"changed\":" << (changed?"true":"false") << ','
              << "\"changed_cell\":[" << changed_x << ',' << changed_y << "],"
              << "\"first_found\":" << (first.found?"true":"false") << ','
              << "\"first_cost\":" << first.cost << ','
              << "\"first_visited\":" << first.visited << ','
              << "\"second_found\":" << (second.found?"true":"false") << ','
              << "\"second_cost\":" << second.cost << ','
              << "\"second_visited\":" << second.visited << ','
              << "\"cells\":[";
    for (std::size_t i=0;i<original_map.cells.size();++i) {
        if (i) std::cout << ',';
        const auto& c = original_map.cells[i];
        const int x = static_cast<int>(i % static_cast<std::size_t>(original_map.width));
        const int y = static_cast<int>(i / static_cast<std::size_t>(original_map.width));
        const bool blocked = c.blocked || (changed && x == changed_x && y == changed_y);
        std::cout << '[' << (blocked ? 1 : 0) << ',' << c.base_cost << ']';
    }
    std::cout << "],\"first_path\":[";
    for (std::size_t i=0;i<first.path.size();++i) {
        if (i) std::cout << ',';
        std::cout << '[' << first.path[i].x << ',' << first.path[i].y << ']';
    }
    std::cout << "],\"second_path\":[";
    for (std::size_t i=0;i<second.path.size();++i) {
        if (i) std::cout << ',';
        std::cout << '[' << second.path[i].x << ',' << second.path[i].y << ']';
    }
    std::cout << "]}\n";
}

} // namespace

int main(int argc, char* argv[]) {
    try {
        const auto o = parse_args(argc,argv);
        math_sim::grid_advanced::GenerationOptions gen;
        gen.width=o.width; gen.height=o.height; gen.obstacle_probability=o.obstacles;
        gen.cost_profile="integer"; gen.min_cost=1.0; gen.max_cost=9.0; gen.seed=o.seed;
        gen.one_way_probability=0.0; gen.dynamic_probability=0.0;
        auto map = math_sim::grid_advanced::generate(gen);
        const math_sim::pathfinding_advanced::Point start{0,0};
        const math_sim::pathfinding_advanced::Point goal{o.width-1,o.height-1};
        if (o.algorithm=="lpa_star") {
            math_sim::incremental_pathfinding::LPAStar planner(map,start,goal,o.diagonal);
            run(planner,map,o);
        } else {
            math_sim::incremental_pathfinding::DStarLite planner(map,start,goal,o.diagonal);
            run(planner,map,o);
        }
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
