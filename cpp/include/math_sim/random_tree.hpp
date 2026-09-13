#pragma once

#include <cmath>
#include <functional>
#include <random>
#include <vector>

namespace math_sim::random_tree {

struct Segment {
    double x1;
    double y1;
    double x2;
    double y2;
    int depth;
};

struct BranchSpec {
    double length;
    double angle;
};

using BranchRule = std::function<std::vector<BranchSpec>(
    std::mt19937_64&,
    double current_length,
    double current_angle,
    int depth
)>;

inline void grow_tree(
    std::vector<Segment>& segments,
    std::mt19937_64& rng,
    double x,
    double y,
    double length,
    double angle,
    int depth,
    const BranchRule& branch_rule
) {
    if (depth <= 0) {
        return;
    }

    const double x2 = x + std::cos(angle) * length;
    const double y2 = y + std::sin(angle) * length;
    segments.push_back({x, y, x2, y2, depth});

    if (depth == 1) {
        return;
    }

    for (const BranchSpec& next : branch_rule(rng, length, angle, depth)) {
        if (next.length > 0.0) {
            grow_tree(segments, rng, x2, y2, next.length, next.angle, depth - 1, branch_rule);
        }
    }
}

}  // namespace math_sim::random_tree
