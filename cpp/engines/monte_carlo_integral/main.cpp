#include "math_sim/math_expression.hpp"

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

namespace {

struct Options {
    std::string expression = "4/(1+x**2)";
    double lower = 0.0;
    double upper = 1.0;
    std::uint64_t samples = 100000;
    std::uint64_t seed = std::random_device{}();
    bool seed_explicit = false;
};

std::string json_escape(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 8);
    for (const char ch : value) {
        switch (ch) {
            case '\\': out += "\\\\"; break;
            case '"': out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out += ch; break;
        }
    }
    return out;
}

Options parse_args(int argc, char* argv[]) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto value = [&]() -> std::string {
            if (i + 1 >= argc) {
                throw std::invalid_argument("missing value for " + arg);
            }
            return argv[++i];
        };

        if (arg == "--expression") options.expression = value();
        else if (arg == "--lower") options.lower = std::stod(value());
        else if (arg == "--upper") options.upper = std::stod(value());
        else if (arg == "--samples") options.samples = std::stoull(value());
        else if (arg == "--seed") {
            options.seed = std::stoull(value());
            options.seed_explicit = true;
        } else if (arg == "--help") {
            std::cout
                << "Usage: monte_carlo_integral --expression EXPR "
                   "[--lower X] [--upper X] [--samples N] [--seed N]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("unknown argument: " + arg);
        }
    }

    if (options.samples == 0) {
        throw std::invalid_argument("--samples must be greater than 0");
    }
    if (!(options.lower < options.upper)) {
        throw std::invalid_argument("--lower must be less than --upper");
    }
    return options;
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_args(argc, argv);
        const auto function = math_sim::expression::compile(options.expression);
        std::mt19937_64 rng(options.seed);
        std::uniform_real_distribution<double> uniform(options.lower, options.upper);

        long double mean = 0.0L;
        long double m2 = 0.0L;
        for (std::uint64_t i = 1; i <= options.samples; ++i) {
            const double x = uniform(rng);
            const double y = function(x);
            if (!std::isfinite(y)) {
                throw std::runtime_error(
                    "function produced non-finite values in the selected interval"
                );
            }
            const long double delta = static_cast<long double>(y) - mean;
            mean += delta / static_cast<long double>(i);
            const long double delta2 = static_cast<long double>(y) - mean;
            m2 += delta * delta2;
        }

        const long double width =
            static_cast<long double>(options.upper - options.lower);
        const double estimate = static_cast<double>(width * mean);
        double standard_error = 0.0;
        if (options.samples > 1) {
            const long double variance =
                m2 / static_cast<long double>(options.samples - 1);
            standard_error = static_cast<double>(
                width * std::sqrt(variance / static_cast<long double>(options.samples))
            );
        }

        std::cout << std::setprecision(17)
                  << "{"
                  << "\"simulation\":\"monte_carlo_integral\","
                  << "\"expression\":\"" << json_escape(options.expression) << "\","
                  << "\"lower\":" << options.lower << ","
                  << "\"upper\":" << options.upper << ","
                  << "\"samples\":" << options.samples << ","
                  << "\"seed\":" << options.seed << ","
                  << "\"seed_explicit\":" << (options.seed_explicit ? "true" : "false") << ","
                  << "\"estimate\":" << estimate << ","
                  << "\"standard_error\":" << standard_error
                  << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
