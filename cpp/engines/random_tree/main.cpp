#include "math_sim/random_tree.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Options {
    int depth = 9;
    std::uint64_t seed = std::random_device{}();
    double length = 1.0;
    double length_decay = 0.72;
    double branch_angle_deg = 28.0;
    double angle_jitter_deg = 10.0;
    double length_jitter = 0.15;
};

Options parse_args(int argc, char* argv[]) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto require_value = [&](const std::string& name) -> std::string {
            if (i + 1 >= argc) {
                throw std::invalid_argument("Missing value for " + name);
            }
            return argv[++i];
        };

        if (arg == "--depth") options.depth = std::stoi(require_value(arg));
        else if (arg == "--seed") options.seed = std::stoull(require_value(arg));
        else if (arg == "--length") options.length = std::stod(require_value(arg));
        else if (arg == "--length-decay") options.length_decay = std::stod(require_value(arg));
        else if (arg == "--branch-angle") options.branch_angle_deg = std::stod(require_value(arg));
        else if (arg == "--angle-jitter") options.angle_jitter_deg = std::stod(require_value(arg));
        else if (arg == "--length-jitter") options.length_jitter = std::stod(require_value(arg));
        else if (arg == "--help") {
            std::cout << "Usage: random_tree [--depth N] [--seed N] [--length X] "
                         "[--length-decay X] [--branch-angle DEG] [--angle-jitter DEG] "
                         "[--length-jitter X]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("Unknown argument: " + arg);
        }
    }

    if (options.depth < 1 || options.depth > 18) throw std::invalid_argument("--depth must be between 1 and 18");
    if (options.length <= 0.0) throw std::invalid_argument("--length must be greater than 0");
    if (options.length_decay <= 0.0 || options.length_decay >= 1.0) throw std::invalid_argument("--length-decay must be between 0 and 1");
    if (options.length_jitter < 0.0 || options.length_jitter >= 1.0) throw std::invalid_argument("--length-jitter must be in [0, 1)");
    return options;
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_args(argc, argv);
        std::mt19937_64 rng(options.seed);
        std::vector<math_sim::random_tree::Segment> segments;
        segments.reserve((1u << std::min(options.depth, 20)) - 1u);

        constexpr double pi = 3.14159265358979323846;
        const double base_branch = options.branch_angle_deg * pi / 180.0;

        math_sim::random_tree::BranchRule rule = [&](std::mt19937_64& local_rng, double current_length, double current_angle, int) {
            std::uniform_real_distribution<double> angle_jitter(-options.angle_jitter_deg, options.angle_jitter_deg);
            std::uniform_real_distribution<double> length_scale(1.0 - options.length_jitter, 1.0 + options.length_jitter);

            return std::vector<math_sim::random_tree::BranchSpec>{
                {current_length * options.length_decay * length_scale(local_rng),
                 current_angle + base_branch + angle_jitter(local_rng) * pi / 180.0},
                {current_length * options.length_decay * length_scale(local_rng),
                 current_angle - base_branch + angle_jitter(local_rng) * pi / 180.0},
            };
        };

        math_sim::random_tree::grow_tree(
            segments, rng, 0.0, 0.0, options.length, -pi / 2.0, options.depth, rule
        );

        std::cout << std::setprecision(17)
                  << "{\"simulation\":\"random_tree\","
                  << "\"seed\":" << options.seed << ","
                  << "\"depth\":" << options.depth << ","
                  << "\"segments\":[";

        for (std::size_t i = 0; i < segments.size(); ++i) {
            const auto& s = segments[i];
            if (i != 0) std::cout << ',';
            std::cout << '[' << s.x1 << ',' << s.y1 << ',' << s.x2 << ',' << s.y2 << ',' << s.depth << ']';
        }

        std::cout << "]}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
