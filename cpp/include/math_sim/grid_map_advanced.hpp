#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace math_sim::grid_advanced {

enum Direction : std::uint8_t {
    East = 1u << 0,
    West = 1u << 1,
    South = 1u << 2,
    North = 1u << 3,
    SouthEast = 1u << 4,
    SouthWest = 1u << 5,
    NorthEast = 1u << 6,
    NorthWest = 1u << 7,
    AllDirections = 0xFFu,
};

struct Cell {
    bool blocked = false;
    double base_cost = 1.0;
    std::uint8_t exit_mask = AllDirections;
    double dynamic_amplitude = 0.0;
    double dynamic_period = 1.0;
    double dynamic_phase = 0.0;

    double cost_at(double time) const {
        if (dynamic_amplitude == 0.0) return base_cost;
        constexpr double pi = 3.14159265358979323846;
        const double wave = std::sin((2.0 * pi * time / std::max(dynamic_period, 1e-9)) + dynamic_phase);
        return std::max(0.0, base_cost + dynamic_amplitude * wave);
    }
};

struct GridMap {
    int width = 0;
    int height = 0;
    std::vector<Cell> cells;

    GridMap() = default;
    GridMap(int w, int h) : width(w), height(h), cells(static_cast<std::size_t>(w * h)) {
        if (w <= 0 || h <= 0) throw std::invalid_argument("grid dimensions must be positive");
    }

    bool in_bounds(int x, int y) const { return x >= 0 && y >= 0 && x < width && y < height; }
    int index(int x, int y) const { return y * width + x; }

    Cell& at(int x, int y) {
        if (!in_bounds(x, y)) throw std::out_of_range("cell out of bounds");
        return cells[static_cast<std::size_t>(index(x, y))];
    }
    const Cell& at(int x, int y) const {
        if (!in_bounds(x, y)) throw std::out_of_range("cell out of bounds");
        return cells[static_cast<std::size_t>(index(x, y))];
    }
};

struct GenerationOptions {
    int width = 32;
    int height = 24;
    double obstacle_probability = 0.20;
    std::string cost_profile = "integer"; // continuous | integer | zero_one
    double min_cost = 1.0;
    double max_cost = 9.0;
    double one_way_probability = 0.0;
    double dynamic_probability = 0.0;
    double dynamic_amplitude = 1.0;
    double dynamic_period = 12.0;
    std::uint64_t seed = 42;
};

inline GridMap generate(const GenerationOptions& o) {
    if (o.width < 2 || o.height < 2) throw std::invalid_argument("grid dimensions must be at least 2");
    if (o.obstacle_probability < 0.0 || o.obstacle_probability >= 1.0) throw std::invalid_argument("invalid obstacle probability");
    if (o.one_way_probability < 0.0 || o.one_way_probability > 1.0) throw std::invalid_argument("invalid one-way probability");
    if (o.dynamic_probability < 0.0 || o.dynamic_probability > 1.0) throw std::invalid_argument("invalid dynamic probability");
    if (o.cost_profile != "zero_one" && (o.min_cost <= 0.0 || o.max_cost < o.min_cost)) throw std::invalid_argument("invalid cost range");

    GridMap map(o.width, o.height);
    std::mt19937_64 rng(o.seed);
    std::bernoulli_distribution obstacle(o.obstacle_probability);
    std::bernoulli_distribution one_way(o.one_way_probability);
    std::bernoulli_distribution dynamic(o.dynamic_probability);
    std::bernoulli_distribution bit01(0.5);
    std::uniform_real_distribution<double> real_cost(o.min_cost, o.max_cost);
    std::uniform_int_distribution<int> int_cost(static_cast<int>(std::ceil(o.min_cost)), static_cast<int>(std::floor(o.max_cost)));
    std::uniform_int_distribution<int> cardinal(0, 3);
    std::uniform_real_distribution<double> phase(0.0, 6.28318530717958647692);

    const std::uint8_t cardinal_masks[4] = {East, West, South, North};
    for (auto& cell : map.cells) {
        cell.blocked = obstacle(rng);
        if (o.cost_profile == "zero_one") cell.base_cost = bit01(rng) ? 1.0 : 0.0;
        else if (o.cost_profile == "integer") cell.base_cost = static_cast<double>(int_cost(rng));
        else cell.base_cost = real_cost(rng);

        if (one_way(rng)) cell.exit_mask = cardinal_masks[cardinal(rng)];
        if (dynamic(rng)) {
            cell.dynamic_amplitude = o.dynamic_amplitude;
            cell.dynamic_period = std::max(o.dynamic_period, 1e-9);
            cell.dynamic_phase = phase(rng);
        }
    }

    auto& start = map.at(0, 0);
    auto& goal = map.at(o.width - 1, o.height - 1);
    start.blocked = false; goal.blocked = false;
    start.exit_mask = AllDirections; goal.exit_mask = AllDirections;
    start.base_cost = std::max(0.0, start.base_cost);
    goal.base_cost = std::max(0.0, goal.base_cost);
    return map;
}

} // namespace math_sim::grid_advanced
