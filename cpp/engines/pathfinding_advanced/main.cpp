#include "math_sim/grid_map_advanced.hpp"
#include "math_sim/jump_point_search.hpp"
#include "math_sim/pathfinding_advanced.hpp"

#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

struct Options {
    int width = 32;
    int height = 24;
    double obstacle_probability = 0.20;
    std::string cost_profile = "integer";
    double min_cost = 1.0;
    double max_cost = 9.0;
    double one_way_probability = 0.0;
    double dynamic_probability = 0.0;
    double dynamic_amplitude = 1.0;
    double dynamic_period = 12.0;
    std::uint64_t seed = 42;
    std::string algorithm = "astar";
    bool diagonal = false;
    bool dynamic_costs = false;
    double start_time = 0.0;
};

Options parse_args(int argc, char* argv[]) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto value = [&]() -> std::string {
            if (i + 1 >= argc) throw std::invalid_argument("missing value for " + arg);
            return argv[++i];
        };
        if (arg == "--width") o.width = std::stoi(value());
        else if (arg == "--height") o.height = std::stoi(value());
        else if (arg == "--obstacles") o.obstacle_probability = std::stod(value());
        else if (arg == "--cost-profile") o.cost_profile = value();
        else if (arg == "--min-cost") o.min_cost = std::stod(value());
        else if (arg == "--max-cost") o.max_cost = std::stod(value());
        else if (arg == "--one-way") o.one_way_probability = std::stod(value());
        else if (arg == "--dynamic") o.dynamic_probability = std::stod(value());
        else if (arg == "--dynamic-amplitude") o.dynamic_amplitude = std::stod(value());
        else if (arg == "--dynamic-period") o.dynamic_period = std::stod(value());
        else if (arg == "--seed") o.seed = std::stoull(value());
        else if (arg == "--algorithm") o.algorithm = value();
        else if (arg == "--diagonal") o.diagonal = std::stoi(value()) != 0;
        else if (arg == "--dynamic-costs") o.dynamic_costs = std::stoi(value()) != 0;
        else if (arg == "--start-time") o.start_time = std::stod(value());
        else if (arg == "--help") {
            std::cout << "Usage: pathfinding_advanced [--width N] [--height N] [--obstacles P] "
                         "[--cost-profile continuous|integer|zero_one] [--min-cost X] [--max-cost X] "
                         "[--one-way P] [--dynamic P] [--dynamic-amplitude X] [--dynamic-period X] "
                         "[--seed N] [--algorithm dijkstra|astar|zero_one_bfs|dial|jps] "
                         "[--diagonal 0|1] [--dynamic-costs 0|1] [--start-time T]\n";
            std::exit(0);
        } else throw std::invalid_argument("unknown argument: " + arg);
    }
    if (o.width < 2 || o.height < 2 || o.width > 160 || o.height > 120) {
        throw std::invalid_argument("grid dimensions out of range");
    }
    return o;
}

void print_json(const math_sim::grid_advanced::GridMap& map,
                const math_sim::pathfinding_advanced::SearchResult& result,
                const Options& options) {
    std::cout << std::setprecision(12);
    std::cout << "{\"simulation\":\"pathfinding_advanced\","
              << "\"algorithm\":\"" << options.algorithm << "\","
              << "\"cost_profile\":\"" << options.cost_profile << "\","
              << "\"diagonal\":" << (options.diagonal ? "true" : "false") << ','
              << "\"dynamic_costs\":" << (options.dynamic_costs ? "true" : "false") << ','
              << "\"width\":" << map.width << ','
              << "\"height\":" << map.height << ','
              << "\"seed\":" << options.seed << ','
              << "\"found\":" << (result.found ? "true" : "false") << ','
              << "\"cost\":" << result.cost << ','
              << "\"visited\":" << result.visited << ','
              << "\"cells\":[";
    for (std::size_t i = 0; i < map.cells.size(); ++i) {
        if (i) std::cout << ',';
        const auto& c = map.cells[i];
        std::cout << '[' << (c.blocked ? 1 : 0) << ',' << c.base_cost << ','
                  << static_cast<int>(c.exit_mask) << ',' << c.dynamic_amplitude << ','
                  << c.dynamic_period << ',' << c.dynamic_phase << ']';
    }
    std::cout << "],\"path\":[";
    for (std::size_t i = 0; i < result.path.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[' << result.path[i].x << ',' << result.path[i].y << ']';
    }
    std::cout << "]}\n";
}

} // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_args(argc, argv);
        math_sim::grid_advanced::GenerationOptions gen;
        gen.width = options.width;
        gen.height = options.height;
        gen.obstacle_probability = options.obstacle_probability;
        gen.cost_profile = options.cost_profile;
        gen.min_cost = options.min_cost;
        gen.max_cost = options.max_cost;
        gen.one_way_probability = options.one_way_probability;
        gen.dynamic_probability = options.dynamic_probability;
        gen.dynamic_amplitude = options.dynamic_amplitude;
        gen.dynamic_period = options.dynamic_period;
        gen.seed = options.seed;
        auto map = math_sim::grid_advanced::generate(gen);

        math_sim::pathfinding_advanced::SearchOptions search;
        search.diagonal = options.diagonal;
        search.dynamic_costs = options.dynamic_costs;
        search.start_time = options.start_time;

        const math_sim::pathfinding_advanced::Point start{0,0};
        const math_sim::pathfinding_advanced::Point goal{options.width - 1, options.height - 1};
        const int max_edge_cost = static_cast<int>(options.max_cost);
        math_sim::pathfinding_advanced::SearchResult result;
        if (options.algorithm == "jps") {
            if (!options.diagonal) throw std::invalid_argument("JPS requires --diagonal 1");
            result = math_sim::jps::search(map, start, goal);
        } else {
            result = math_sim::pathfinding_advanced::solve(
                map, start, goal, options.algorithm, search, max_edge_cost
            );
        }
        print_json(map, result, options);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
