#include "math_sim/grid_map.hpp"
#include "math_sim/pathfinding.hpp"
#include "math_sim/pathfinding_extra.hpp"

#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

namespace {

struct Options {
    int width = 32;
    int height = 24;
    double obstacle_probability = 0.22;
    double min_cost = 1.0;
    double max_cost = 5.0;
    std::uint64_t seed = 42;
    std::string algorithm = "dijkstra";
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
        else if (arg == "--min-cost") o.min_cost = std::stod(value());
        else if (arg == "--max-cost") o.max_cost = std::stod(value());
        else if (arg == "--seed") o.seed = std::stoull(value());
        else if (arg == "--algorithm") o.algorithm = value();
        else if (arg == "--help") {
            std::cout << "Usage: pathfinding [--width N] [--height N] [--obstacles P] "
                         "[--min-cost X] [--max-cost X] [--seed N] "
                         "[--algorithm dijkstra|bidijkstra|astar|weighted_astar|bfs|bibfs|dfs|greedy|"
                         "bellman_ford|spfa|iddfs|ida_star|fringe]\n";
            std::exit(0);
        } else throw std::invalid_argument("unknown argument: " + arg);
    }
    if (o.width < 2 || o.height < 2 || o.width > 160 || o.height > 120) {
        throw std::invalid_argument("grid dimensions out of range");
    }
    return o;
}

bool is_extra_algorithm(const std::string& algorithm) {
    return algorithm == "bellman_ford" || algorithm == "spfa" ||
           algorithm == "iddfs" || algorithm == "ida_star" || algorithm == "fringe";
}

void print_json(const math_sim::grid::GridMap& map,
                const math_sim::pathfinding::SearchResult& result,
                const Options& options) {
    std::cout << std::setprecision(12);
    std::cout << "{\"simulation\":\"pathfinding\","
              << "\"algorithm\":\"" << options.algorithm << "\","
              << "\"width\":" << map.width << ","
              << "\"height\":" << map.height << ","
              << "\"seed\":" << options.seed << ","
              << "\"found\":" << (result.found ? "true" : "false") << ","
              << "\"cost\":" << result.cost << ","
              << "\"visited\":" << result.visited << ","
              << "\"cells\":[";
    for (std::size_t i = 0; i < map.cells.size(); ++i) {
        if (i) std::cout << ',';
        const auto& c = map.cells[i];
        std::cout << '[' << (c.blocked ? 1 : 0) << ',' << c.cost << ']';
    }
    std::cout << "],\"path\":[";
    for (std::size_t i = 0; i < result.path.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[' << result.path[i].x << ',' << result.path[i].y << ']';
    }
    std::cout << "]}\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_args(argc, argv);
        auto map = math_sim::grid::generate_random_map(
            options.width,
            options.height,
            options.obstacle_probability,
            options.min_cost,
            options.max_cost,
            options.seed
        );
        const math_sim::pathfinding::Point start{0, 0};
        const math_sim::pathfinding::Point goal{options.width - 1, options.height - 1};
        const auto result = is_extra_algorithm(options.algorithm)
            ? math_sim::pathfinding::extra::solve(map, start, goal, options.algorithm)
            : math_sim::pathfinding::solve(map, start, goal, options.algorithm);
        print_json(map, result, options);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
