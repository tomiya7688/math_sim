#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "math_sim/mlp.hpp"

namespace {

struct Options {
    std::string gate = "XOR";
    std::size_t hidden = 2;
    double learning_rate = 0.5;
    std::size_t epochs = 5000;
    std::uint64_t seed = 42;
};

Options parse_args(int argc, char* argv[]) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto value = [&]() -> std::string {
            if (i + 1 >= argc) throw std::invalid_argument("missing value for " + arg);
            return argv[++i];
        };
        if (arg == "--gate") o.gate = value();
        else if (arg == "--hidden") o.hidden = static_cast<std::size_t>(std::stoull(value()));
        else if (arg == "--learning-rate") o.learning_rate = std::stod(value());
        else if (arg == "--epochs") o.epochs = static_cast<std::size_t>(std::stoull(value()));
        else if (arg == "--seed") o.seed = std::stoull(value());
        else throw std::invalid_argument("unknown argument: " + arg);
    }
    return o;
}

std::vector<double> targets_for(const std::string& gate) {
    if (gate == "AND") return {0, 0, 0, 1};
    if (gate == "OR") return {0, 1, 1, 1};
    if (gate == "NAND") return {1, 1, 1, 0};
    if (gate == "XOR") return {0, 1, 1, 0};
    throw std::invalid_argument("gate must be AND, OR, NAND, or XOR");
}

void print_array(const std::vector<double>& v) {
    std::cout << '[';
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << v[i];
    }
    std::cout << ']';
}

}  // namespace

int main(int argc, char* argv[]) {
    try {
        const auto o = parse_args(argc, argv);
        const std::vector<std::vector<double>> samples{{0,0},{0,1},{1,0},{1,1}};
        const auto targets = targets_for(o.gate);
        const auto r = math_sim::mlp::train_binary_classifier(samples, targets, o.hidden, o.learning_rate, o.epochs, o.seed);

        std::cout << std::setprecision(17);
        std::cout << "{\"simulation\":\"mlp\",\"gate\":\"" << o.gate << "\",\"hidden\":" << o.hidden
                  << ",\"epochs\":" << o.epochs << ",\"learning_rate\":" << o.learning_rate
                  << ",\"seed\":" << o.seed << ",\"w1\":";
        print_array(r.w1);
        std::cout << ",\"b1\":"; print_array(r.b1);
        std::cout << ",\"w2\":"; print_array(r.w2);
        std::cout << ",\"b2\":" << r.b2 << ",\"loss_history\":"; print_array(r.loss_history);
        std::cout << ",\"predictions\":"; print_array(r.predictions);
        std::cout << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
