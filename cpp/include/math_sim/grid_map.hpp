#pragma once

#include <algorithm>
#include <cstdint>
#include <random>
#include <stdexcept>
#include <vector>

namespace math_sim::grid {

struct Cell {
    bool blocked = false;
    double cost = 1.0;
};

struct GridMap {
    int width = 0;
    int height = 0;
    std::vector<Cell> cells;

    GridMap() = default;
    GridMap(int w, int h) : width(w), height(h), cells(static_cast<std::size_t>(w * h)) {
        if (w <= 0 || h <= 0) {
            throw std::invalid_argument("grid dimensions must be positive");
        }
    }

    bool in_bounds(int x, int y) const {
        return x >= 0 && y >= 0 && x < width && y < height;
    }

    int index(int x, int y) const {
        return y * width + x;
    }

    Cell& at(int x, int y) {
        if (!in_bounds(x, y)) throw std::out_of_range("cell out of bounds");
        return cells[static_cast<std::size_t>(index(x, y))];
    }

    const Cell& at(int x, int y) const {
        if (!in_bounds(x, y)) throw std::out_of_range("cell out of bounds");
        return cells[static_cast<std::size_t>(index(x, y))];
    }
};

inline GridMap generate_random_map(
    int width,
    int height,
    double obstacle_probability,
    double min_cost,
    double max_cost,
    std::uint64_t seed
) {
    if (obstacle_probability < 0.0 || obstacle_probability >= 1.0) {
        throw std::invalid_argument("obstacle_probability must be in [0, 1)");
    }
    if (min_cost <= 0.0 || max_cost < min_cost) {
        throw std::invalid_argument("invalid cost range");
    }

    GridMap map(width, height);
    std::mt19937_64 rng(seed);
    std::bernoulli_distribution blocked(obstacle_probability);
    std::uniform_real_distribution<double> cost_dist(min_cost, max_cost);

    for (auto& cell : map.cells) {
        cell.blocked = blocked(rng);
        cell.cost = cost_dist(rng);
    }

    map.at(0, 0).blocked = false;
    map.at(width - 1, height - 1).blocked = false;
    map.at(0, 0).cost = 1.0;
    map.at(width - 1, height - 1).cost = 1.0;
    return map;
}

}  // namespace math_sim::grid
