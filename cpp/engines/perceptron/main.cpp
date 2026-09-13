#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "math_sim/perceptron.hpp"

namespace {

struct Options {
    std::string gate = "AND";
    double learning_rate = 0.1;
    int epochs = 100;
};

Options parse_args(int argc, char* argv[]) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto value = [&](const std::string& name) -> std::string {
            if (i + 1 >= argc) {
                throw std::invalid_argument("Missing value for " + name);
            }
            return argv[++i];
        };
        if (arg == "--gate") {
            options.gate = value(arg);
        } else if (arg == "--learning-rate") {
            options.learning_rate = std::stod(value(arg));
        } else if (arg == "--epochs") {
            options.epochs = std::stoi(value(arg));
        } else if (arg == "--help") {
            std::cout << "Usage: perceptron [--gate AND|OR|NAND|XOR] [--learning-rate X] [--epochs N]\n";
            std::exit(0);
        } else {
            throw std::invalid_argument("Unknown argument: " + arg);
        }
    }
    return options;
}

std::vector<int> gate_targets(std::string gate) {
    for (char& c : gate) {
        if (c >= 'a' && c <= 'z') c = static_cast<char>(c - 'a' + 'A');
    }
    if (gate == "AND") return {0, 0, 0, 1};
    if (gate == "OR") return {0, 1, 1, 1};
    if (gate == "NAND") return {1, 1, 1, 0};
    if (gate == "XOR") return {0, 1, 1, 0};
    throw std::invalid_argument("Unknown gate: " + gate);
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const Options options = parse_args(argc, argv);
        const std::vector<std::vector<double>> samples = {
            {0.0, 0.0}, {0.0, 1.0}, {1.0, 0.0}, {1.0, 1.0}
        };
        const auto targets = gate_targets(options.gate);
        const auto result = math_sim::perceptron::train(
            samples, targets, options.learning_rate, options.epochs
        );

        std::cout << std::setprecision(17)
                  << "{\"simulation\":\"perceptron\",";
        std::cout << "\"gate\":\"" << options.gate << "\",";
        std::cout << "\"weights\":[";
        for (std::size_t i = 0; i < result.weights.size(); ++i) {
            if (i) std::cout << ',';
            std::cout << result.weights[i];
        }
        std::cout << "],\"bias\":" << result.bias
                  << ",\"converged\":" << (result.converged ? "true" : "false")
                  << ",\"errors_per_epoch\":[";
        for (std::size_t i = 0; i < result.errors_per_epoch.size(); ++i) {
            if (i) std::cout << ',';
            std::cout << result.errors_per_epoch[i];
        }
        std::cout << "],\"predictions\":[";
        for (std::size_t i = 0; i < samples.size(); ++i) {
            if (i) std::cout << ',';
            std::cout << math_sim::perceptron::predict(samples[i], result.weights, result.bias);
        }
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
