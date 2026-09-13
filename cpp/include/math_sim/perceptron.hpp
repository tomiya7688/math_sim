#pragma once

#include <cstddef>
#include <stdexcept>
#include <vector>

namespace math_sim::perceptron {

struct TrainResult {
    std::vector<double> weights;
    double bias = 0.0;
    std::vector<int> errors_per_epoch;
    bool converged = false;
};

inline int step(double value) {
    return value >= 0.0 ? 1 : 0;
}

inline int predict(const std::vector<double>& inputs,
                   const std::vector<double>& weights,
                   double bias) {
    if (inputs.size() != weights.size()) {
        throw std::invalid_argument("inputs and weights must have the same length");
    }
    double activation = bias;
    for (std::size_t i = 0; i < inputs.size(); ++i) {
        activation += inputs[i] * weights[i];
    }
    return step(activation);
}

inline TrainResult train(const std::vector<std::vector<double>>& samples,
                         const std::vector<int>& targets,
                         double learning_rate,
                         int epochs,
                         std::vector<double> weights = {},
                         double bias = 0.0) {
    if (samples.empty()) {
        throw std::invalid_argument("samples must not be empty");
    }
    if (samples.size() != targets.size()) {
        throw std::invalid_argument("targets must contain one value per sample");
    }
    if (learning_rate <= 0.0 || epochs <= 0) {
        throw std::invalid_argument("learning_rate and epochs must be positive");
    }

    const auto feature_count = samples.front().size();
    if (feature_count == 0) {
        throw std::invalid_argument("samples must contain at least one feature");
    }
    for (const auto& sample : samples) {
        if (sample.size() != feature_count) {
            throw std::invalid_argument("all samples must have the same feature count");
        }
    }
    for (const int target : targets) {
        if (target != 0 && target != 1) {
            throw std::invalid_argument("targets must be 0 or 1");
        }
    }

    if (weights.empty()) {
        weights.assign(feature_count, 0.0);
    } else if (weights.size() != feature_count) {
        throw std::invalid_argument("initial weights have the wrong size");
    }

    TrainResult result;
    for (int epoch = 0; epoch < epochs; ++epoch) {
        int errors = 0;
        for (std::size_t i = 0; i < samples.size(); ++i) {
            const int output = predict(samples[i], weights, bias);
            const int delta = targets[i] - output;
            if (delta != 0) {
                for (std::size_t j = 0; j < feature_count; ++j) {
                    weights[j] += learning_rate * static_cast<double>(delta) * samples[i][j];
                }
                bias += learning_rate * static_cast<double>(delta);
                ++errors;
            }
        }
        result.errors_per_epoch.push_back(errors);
        if (errors == 0) {
            result.converged = true;
            break;
        }
    }

    result.weights = std::move(weights);
    result.bias = bias;
    return result;
}

}  // namespace math_sim::perceptron
