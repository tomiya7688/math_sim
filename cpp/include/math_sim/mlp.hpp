#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <random>
#include <stdexcept>
#include <vector>

namespace math_sim::mlp {

struct TrainResult {
    std::vector<double> w1;
    std::vector<double> b1;
    std::vector<double> w2;
    double b2 = 0.0;
    std::vector<double> loss_history;
    std::vector<double> predictions;
};

inline double sigmoid(double x) {
    if (x >= 0.0) {
        const double z = std::exp(-x);
        return 1.0 / (1.0 + z);
    }
    const double z = std::exp(x);
    return z / (1.0 + z);
}

inline TrainResult train_binary_classifier(
    const std::vector<std::vector<double>>& samples,
    const std::vector<double>& targets,
    std::size_t hidden_units = 2,
    double learning_rate = 0.5,
    std::size_t epochs = 5000,
    std::uint64_t seed = 42
) {
    if (samples.empty() || samples.size() != targets.size()) {
        throw std::invalid_argument("samples and targets must be non-empty and equal in size");
    }
    const std::size_t inputs = samples.front().size();
    if (inputs == 0 || hidden_units == 0 || learning_rate <= 0.0 || epochs == 0) {
        throw std::invalid_argument("invalid network or training parameters");
    }
    for (const auto& x : samples) if (x.size() != inputs) throw std::invalid_argument("inconsistent input dimensions");

    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> init(-1.0, 1.0);
    TrainResult r;
    r.w1.resize(hidden_units * inputs);
    r.b1.assign(hidden_units, 0.0);
    r.w2.resize(hidden_units);
    for (double& v : r.w1) v = init(rng);
    for (double& v : r.w2) v = init(rng);
    r.loss_history.reserve(epochs);

    std::vector<double> h(hidden_units);
    for (std::size_t epoch = 0; epoch < epochs; ++epoch) {
        double loss = 0.0;
        for (std::size_t n = 0; n < samples.size(); ++n) {
            const auto& x = samples[n];
            for (std::size_t j = 0; j < hidden_units; ++j) {
                double z = r.b1[j];
                for (std::size_t i = 0; i < inputs; ++i) z += r.w1[j * inputs + i] * x[i];
                h[j] = sigmoid(z);
            }
            double zo = r.b2;
            for (std::size_t j = 0; j < hidden_units; ++j) zo += r.w2[j] * h[j];
            const double y = sigmoid(zo);
            const double t = targets[n];
            const double e = y - t;
            loss += -(t * std::log(std::max(y, 1e-12)) + (1.0 - t) * std::log(std::max(1.0 - y, 1e-12)));

            const double delta_out = e;
            std::vector<double> delta_h(hidden_units);
            for (std::size_t j = 0; j < hidden_units; ++j)
                delta_h[j] = r.w2[j] * delta_out * h[j] * (1.0 - h[j]);

            for (std::size_t j = 0; j < hidden_units; ++j) r.w2[j] -= learning_rate * delta_out * h[j];
            r.b2 -= learning_rate * delta_out;
            for (std::size_t j = 0; j < hidden_units; ++j) {
                for (std::size_t i = 0; i < inputs; ++i)
                    r.w1[j * inputs + i] -= learning_rate * delta_h[j] * x[i];
                r.b1[j] -= learning_rate * delta_h[j];
            }
        }
        r.loss_history.push_back(loss / samples.size());
    }

    r.predictions.reserve(samples.size());
    for (const auto& x : samples) {
        for (std::size_t j = 0; j < hidden_units; ++j) {
            double z = r.b1[j];
            for (std::size_t i = 0; i < inputs; ++i) z += r.w1[j * inputs + i] * x[i];
            h[j] = sigmoid(z);
        }
        double zo = r.b2;
        for (std::size_t j = 0; j < hidden_units; ++j) zo += r.w2[j] * h[j];
        r.predictions.push_back(sigmoid(zo));
    }
    return r;
}

}  // namespace math_sim::mlp
