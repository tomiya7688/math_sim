#pragma once

#include <algorithm>
#include <cctype>
#include <cmath>
#include <functional>
#include <stdexcept>
#include <string>
#include <string_view>

namespace math_sim::expression {

using Function = std::function<double(double)>;

class Parser {
public:
    explicit Parser(std::string expression) : source_(std::move(expression)) {}

    Function parse() {
        skip_ws();
        if (source_.empty()) {
            throw std::invalid_argument("function expression must not be empty");
        }
        Function result = parse_expression();
        skip_ws();
        if (!eof()) {
            throw error("unexpected trailing input");
        }
        return result;
    }

private:
    Function parse_expression() {
        Function lhs = parse_term();
        while (true) {
            skip_ws();
            if (consume('+')) {
                Function rhs = parse_term();
                Function left = std::move(lhs);
                lhs = [left = std::move(left), rhs = std::move(rhs)](double x) {
                    return left(x) + rhs(x);
                };
            } else if (consume('-')) {
                Function rhs = parse_term();
                Function left = std::move(lhs);
                lhs = [left = std::move(left), rhs = std::move(rhs)](double x) {
                    return left(x) - rhs(x);
                };
            } else {
                return lhs;
            }
        }
    }

    Function parse_term() {
        Function lhs = parse_unary();
        while (true) {
            skip_ws();
            if (peek("**")) {
                return lhs;
            }
            if (consume('*')) {
                Function rhs = parse_unary();
                Function left = std::move(lhs);
                lhs = [left = std::move(left), rhs = std::move(rhs)](double x) {
                    return left(x) * rhs(x);
                };
            } else if (consume('/')) {
                Function rhs = parse_unary();
                Function left = std::move(lhs);
                lhs = [left = std::move(left), rhs = std::move(rhs)](double x) {
                    return left(x) / rhs(x);
                };
            } else if (consume('%')) {
                Function rhs = parse_unary();
                Function left = std::move(lhs);
                lhs = [left = std::move(left), rhs = std::move(rhs)](double x) {
                    return std::fmod(left(x), rhs(x));
                };
            } else {
                return lhs;
            }
        }
    }

    Function parse_unary() {
        skip_ws();
        if (consume('+')) {
            return parse_unary();
        }
        if (consume('-')) {
            Function value = parse_unary();
            return [value = std::move(value)](double x) { return -value(x); };
        }
        return parse_power();
    }

    Function parse_power() {
        Function base = parse_primary();
        skip_ws();
        if (consume_string("**")) {
            Function exponent = parse_unary();
            return [base = std::move(base), exponent = std::move(exponent)](double x) {
                return std::pow(base(x), exponent(x));
            };
        }
        return base;
    }

    Function parse_primary() {
        skip_ws();
        if (consume('(')) {
            Function value = parse_expression();
            require(')');
            return value;
        }

        if (!eof() && (std::isdigit(static_cast<unsigned char>(current())) || current() == '.')) {
            const double value = parse_number();
            return [value](double) { return value; };
        }

        if (!eof() && (std::isalpha(static_cast<unsigned char>(current())) || current() == '_')) {
            const std::string name = parse_identifier();
            if (name == "x") return [](double x) { return x; };
            if (name == "pi") return [](double) { return std::acos(-1.0); };
            if (name == "e") return [](double) { return std::exp(1.0); };

            skip_ws();
            require('(');
            Function first = parse_expression();
            skip_ws();
            if (name == "minimum" || name == "maximum") {
                require(',');
                Function second = parse_expression();
                require(')');
                if (name == "minimum") {
                    return [first = std::move(first), second = std::move(second)](double x) {
                        return std::min(first(x), second(x));
                    };
                }
                return [first = std::move(first), second = std::move(second)](double x) {
                    return std::max(first(x), second(x));
                };
            }
            require(')');
            return unary_function(name, std::move(first));
        }

        throw error("expected number, variable, function, or parenthesized expression");
    }

    static Function unary_function(const std::string& name, Function arg) {
        if (name == "sin") return [arg = std::move(arg)](double x) { return std::sin(arg(x)); };
        if (name == "cos") return [arg = std::move(arg)](double x) { return std::cos(arg(x)); };
        if (name == "tan") return [arg = std::move(arg)](double x) { return std::tan(arg(x)); };
        if (name == "asin") return [arg = std::move(arg)](double x) { return std::asin(arg(x)); };
        if (name == "acos") return [arg = std::move(arg)](double x) { return std::acos(arg(x)); };
        if (name == "atan") return [arg = std::move(arg)](double x) { return std::atan(arg(x)); };
        if (name == "sinh") return [arg = std::move(arg)](double x) { return std::sinh(arg(x)); };
        if (name == "cosh") return [arg = std::move(arg)](double x) { return std::cosh(arg(x)); };
        if (name == "tanh") return [arg = std::move(arg)](double x) { return std::tanh(arg(x)); };
        if (name == "exp") return [arg = std::move(arg)](double x) { return std::exp(arg(x)); };
        if (name == "log") return [arg = std::move(arg)](double x) { return std::log(arg(x)); };
        if (name == "log10") return [arg = std::move(arg)](double x) { return std::log10(arg(x)); };
        if (name == "sqrt") return [arg = std::move(arg)](double x) { return std::sqrt(arg(x)); };
        if (name == "abs") return [arg = std::move(arg)](double x) { return std::abs(arg(x)); };
        if (name == "floor") return [arg = std::move(arg)](double x) { return std::floor(arg(x)); };
        if (name == "ceil") return [arg = std::move(arg)](double x) { return std::ceil(arg(x)); };
        throw std::invalid_argument("unknown function: " + name);
    }

    double parse_number() {
        const std::size_t start = pos_;
        bool seen_digit = false;
        while (!eof() && std::isdigit(static_cast<unsigned char>(current()))) {
            ++pos_;
            seen_digit = true;
        }
        if (!eof() && current() == '.') {
            ++pos_;
            while (!eof() && std::isdigit(static_cast<unsigned char>(current()))) {
                ++pos_;
                seen_digit = true;
            }
        }
        if (!seen_digit) throw error("invalid number");
        if (!eof() && (current() == 'e' || current() == 'E')) {
            ++pos_;
            if (!eof() && (current() == '+' || current() == '-')) ++pos_;
            const std::size_t exponent_start = pos_;
            while (!eof() && std::isdigit(static_cast<unsigned char>(current()))) ++pos_;
            if (exponent_start == pos_) throw error("invalid exponent");
        }
        return std::stod(source_.substr(start, pos_ - start));
    }

    std::string parse_identifier() {
        const std::size_t start = pos_;
        while (!eof()) {
            const char ch = current();
            if (!std::isalnum(static_cast<unsigned char>(ch)) && ch != '_') break;
            ++pos_;
        }
        return source_.substr(start, pos_ - start);
    }

    void skip_ws() {
        while (!eof() && std::isspace(static_cast<unsigned char>(current()))) ++pos_;
    }

    bool consume(char ch) {
        skip_ws();
        if (!eof() && current() == ch) {
            ++pos_;
            return true;
        }
        return false;
    }

    bool consume_string(std::string_view value) {
        skip_ws();
        if (peek(value)) {
            pos_ += value.size();
            return true;
        }
        return false;
    }

    bool peek(std::string_view value) const {
        return source_.compare(pos_, value.size(), value) == 0;
    }

    void require(char ch) {
        if (!consume(ch)) {
            throw error(std::string("expected '") + ch + "'");
        }
    }

    char current() const { return source_[pos_]; }
    bool eof() const noexcept { return pos_ >= source_.size(); }

    std::invalid_argument error(const std::string& message) const {
        return std::invalid_argument(message + " at position " + std::to_string(pos_));
    }

    std::string source_;
    std::size_t pos_{0};
};

inline Function compile(std::string expression) {
    return Parser(std::move(expression)).parse();
}

}  // namespace math_sim::expression
