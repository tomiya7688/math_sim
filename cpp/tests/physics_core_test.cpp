#include <cassert>
#include <cmath>
#include <stdexcept>

#include "math_sim/physics.hpp"

namespace {

bool near(double a, double b, double eps = 1e-9) {
    return std::abs(a - b) <= eps;
}

}  // namespace

int main() {
    using namespace math_sim::physics;

    EulerPhysicsWorld world;
    world.set_gravity({0.0, -10.0});

    const auto id = world.create_body(BodyDefinition{
        BodyType::Dynamic,
        {1.0, 2.0},
        {3.0, 4.0},
        2.0,
        0.0,
    });

    world.step(0.5);
    auto state = world.body_state(id);
    assert(near(state.velocity.x, 3.0));
    assert(near(state.velocity.y, -1.0));
    assert(near(state.position.x, 2.5));
    assert(near(state.position.y, 1.5));

    world.pause(true);
    world.step(1.0);
    const auto paused = world.body_state(id);
    assert(near(paused.position.x, state.position.x));
    assert(near(paused.position.y, state.position.y));

    world.reset();
    state = world.body_state(id);
    assert(near(state.position.x, 1.0));
    assert(near(state.position.y, 2.0));
    assert(near(state.velocity.x, 3.0));
    assert(near(state.velocity.y, 4.0));
    assert(!world.is_paused());

    const auto static_id = world.create_body(BodyDefinition{
        BodyType::Static,
        {5.0, 6.0},
        {},
        1.0,
        0.0,
    });
    world.step(1.0);
    const auto static_state = world.body_state(static_id);
    assert(near(static_state.position.x, 5.0));
    assert(near(static_state.position.y, 6.0));

    bool rejected = false;
    try {
        world.create_body(BodyDefinition{
            BodyType::Dynamic, {}, {}, 0.0, 0.0
        });
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    assert(rejected);

    world.remove_body(id);

    // Repeated lifecycle exercise for sanitizer/LSan coverage.
    for (int iteration = 0; iteration < 1000; ++iteration) {
        EulerPhysicsWorld repeated;
        repeated.set_gravity({0.0, -9.81});
        const auto repeated_id = repeated.create_body(BodyDefinition{
            BodyType::Dynamic,
            {0.0, 1.0},
            {1.0, 0.0},
            1.0,
            0.01,
        });
        repeated.step(1.0 / 60.0);
        repeated.pause(true);
        repeated.step(1.0 / 60.0);
        repeated.pause(false);
        repeated.reset();
        (void)repeated.body_state(repeated_id);
        repeated.remove_body(repeated_id);
    }

    bool missing = false;
    try {
        (void)world.body_state(id);
    } catch (const std::out_of_range&) {
        missing = true;
    }
    assert(missing);

    return 0;
}
