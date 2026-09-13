#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>

namespace {

struct Options {
    std::uint64_t samples = 1'000'000;
    std::uint64_t seed = std::random_device{}();
};

Options parse_args(int argc, char* argv[]) {
    Options options;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--samples" && i + 1 < argc) {
            options.samples = std::stoull(argv[++i]);
        } else if (arg == "--seed" && i + 1 < argc) {
            options.seed = std::stoull(argv[++i]);
        } else if (arg == "--help") {
            std::cout << "Usage: monte_carlo_pi [--samples N] [--seed N]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("Unknown or incomplete argument: " + arg);
        }
    }

    if (options.samples == 0) {
        throw std::invalid_argument("--samples must be greater than 0");
    }

    return options;
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_args(argc, argv);

        std::mt19937_64 rng(options.seed);
        std::uniform_real_distribution<double> uniform(0.0, 1.0);

        std::uint64_t inside = 0;
        for (std::uint64_t i = 0; i < options.samples; ++i) {
            const double x = uniform(rng);
            const double y = uniform(rng);
            if (x * x + y * y <= 1.0) {
                ++inside;
            }
        }

        const double pi_estimate = 4.0 * static_cast<double>(inside) /
                                   static_cast<double>(options.samples);
        const double absolute_error = std::abs(pi_estimate - std::acos(-1.0));

        std::cout << std::setprecision(17)
                  << "{"
                  << "\"simulation\":\"monte_carlo_pi\","
                  << "\"samples\":" << options.samples << ","
                  << "\"inside\":" << inside << ","
                  << "\"seed\":" << options.seed << ","
                  << "\"pi_estimate\":" << pi_estimate << ","
                  << "\"absolute_error\":" << absolute_error
                  << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
