#pragma once

#include <cstdint>
#include <random>
#include <stdexcept>

namespace math_sim::monte_carlo {

template <class Predicate>
std::uint64_t count_hits(
    std::uint64_t samples,
    std::mt19937_64& rng,
    Predicate&& predicate
) {
    if (samples == 0) {
        throw std::invalid_argument("samples must be greater than 0");
    }

    std::uniform_real_distribution<double> uniform(0.0, 1.0);
    std::uint64_t hits = 0;
    for (std::uint64_t i = 0; i < samples; ++i) {
        if (predicate(uniform(rng), uniform(rng))) {
            ++hits;
        }
    }
    return hits;
}

template <class Function>
double integrate_1d(
    std::uint64_t samples,
    std::mt19937_64& rng,
    double lower,
    double upper,
    Function&& function
) {
    if (samples == 0) {
        throw std::invalid_argument("samples must be greater than 0");
    }
    if (!(lower < upper)) {
        throw std::invalid_argument("lower must be less than upper");
    }

    std::uniform_real_distribution<double> uniform(lower, upper);
    long double sum = 0.0L;
    for (std::uint64_t i = 0; i < samples; ++i) {
        sum += static_cast<long double>(function(uniform(rng)));
    }
    return (upper - lower) * static_cast<double>(sum / samples);
}

}  // namespace math_sim::monte_carlo
