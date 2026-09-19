#pragma once

#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <unordered_map>

namespace math_sim::physics {

struct Vec2 {
    double x{0.0};
    double y{0.0};

    Vec2& operator+=(const Vec2& other) noexcept {
        x += other.x;
        y += other.y;
        return *this;
    }
};

inline Vec2 operator+(Vec2 lhs, const Vec2& rhs) noexcept {
    lhs += rhs;
    return lhs;
}

inline Vec2 operator*(Vec2 value, double scalar) noexcept {
    value.x *= scalar;
    value.y *= scalar;
    return value;
}

enum class BodyType {
    Static,
    Dynamic,
};

using BodyId = std::size_t;

struct BodyDefinition {
    BodyType type{BodyType::Dynamic};
    Vec2 position{};
    Vec2 velocity{};
    double mass{1.0};
    double linear_damping{0.0};
};

struct BodyState {
    BodyType type{BodyType::Dynamic};
    Vec2 position{};
    Vec2 velocity{};
    double mass{1.0};
};

class PhysicsWorld {
public:
    virtual ~PhysicsWorld() = default;

    virtual BodyId create_body(const BodyDefinition& definition) = 0;
    virtual void remove_body(BodyId id) = 0;
    virtual BodyState body_state(BodyId id) const = 0;

    virtual void set_gravity(Vec2 gravity) = 0;
    virtual Vec2 gravity() const noexcept = 0;

    virtual void step(double dt_seconds) = 0;
    virtual void pause(bool paused) noexcept = 0;
    virtual bool is_paused() const noexcept = 0;
    virtual void reset() = 0;
};

/**
 * Dependency-free educational backend.
 *
 * This backend intentionally implements only point-mass translation with
 * semi-implicit Euler integration. It provides a stable common API while
 * Box2D/Jolt adapters remain optional. It is not a collision engine.
 */
class EulerPhysicsWorld final : public PhysicsWorld {
public:
    BodyId create_body(const BodyDefinition& definition) override {
        validate_definition(definition);
        const BodyId id = next_id_++;
        bodies_.emplace(id, BodyRecord{definition, to_state(definition)});
        return id;
    }

    void remove_body(BodyId id) override {
        if (bodies_.erase(id) == 0) {
            throw std::out_of_range("unknown physics body id");
        }
    }

    BodyState body_state(BodyId id) const override {
        return record(id).state;
    }

    void set_gravity(Vec2 gravity) override {
        if (!finite(gravity.x) || !finite(gravity.y)) {
            throw std::invalid_argument("gravity must be finite");
        }
        gravity_ = gravity;
    }

    Vec2 gravity() const noexcept override {
        return gravity_;
    }

    void step(double dt_seconds) override {
        if (!finite(dt_seconds) || dt_seconds < 0.0) {
            throw std::invalid_argument("time step must be finite and non-negative");
        }
        if (paused_ || dt_seconds == 0.0) {
            return;
        }

        for (auto& [id, body] : bodies_) {
            (void)id;
            if (body.state.type == BodyType::Static) {
                continue;
            }

            body.state.velocity += gravity_ * dt_seconds;
            if (body.definition.linear_damping > 0.0) {
                const double damping =
                    1.0 / (1.0 + body.definition.linear_damping * dt_seconds);
                body.state.velocity = body.state.velocity * damping;
            }
            body.state.position += body.state.velocity * dt_seconds;
        }
    }

    void pause(bool paused) noexcept override {
        paused_ = paused;
    }

    bool is_paused() const noexcept override {
        return paused_;
    }

    void reset() override {
        for (auto& [id, body] : bodies_) {
            (void)id;
            body.state = to_state(body.definition);
        }
        paused_ = false;
    }

private:
    struct BodyRecord {
        BodyDefinition definition;
        BodyState state;
    };

    static bool finite(double value) noexcept {
        return std::isfinite(value);
    }

    static void validate_definition(const BodyDefinition& definition) {
        if (!finite(definition.position.x) || !finite(definition.position.y) ||
            !finite(definition.velocity.x) || !finite(definition.velocity.y)) {
            throw std::invalid_argument("body position and velocity must be finite");
        }
        if (!finite(definition.mass) || definition.mass <= 0.0) {
            throw std::invalid_argument("body mass must be finite and positive");
        }
        if (!finite(definition.linear_damping) || definition.linear_damping < 0.0) {
            throw std::invalid_argument("linear damping must be finite and non-negative");
        }
    }

    static BodyState to_state(const BodyDefinition& definition) noexcept {
        return BodyState{
            definition.type,
            definition.position,
            definition.velocity,
            definition.mass,
        };
    }

    const BodyRecord& record(BodyId id) const {
        const auto it = bodies_.find(id);
        if (it == bodies_.end()) {
            throw std::out_of_range("unknown physics body id");
        }
        return it->second;
    }

    std::unordered_map<BodyId, BodyRecord> bodies_;
    BodyId next_id_{1};
    Vec2 gravity_{0.0, -9.80665};
    bool paused_{false};
};

}  // namespace math_sim::physics
