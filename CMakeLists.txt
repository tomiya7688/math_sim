cmake_minimum_required(VERSION 3.20)
project(math_sim_engines LANGUAGES CXX)

include(CTest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(cpp/engines/monte_carlo_pi)
add_subdirectory(cpp/engines/monte_carlo_integral)
add_subdirectory(cpp/engines/random_tree)
add_subdirectory(cpp/engines/perceptron)
add_subdirectory(cpp/engines/mlp)
add_subdirectory(cpp/engines/pathfinding)
add_subdirectory(cpp/engines/pathfinding_advanced)
add_subdirectory(cpp/engines/pathfinding_replanning)
add_subdirectory(cpp/engines/maze)

if(BUILD_TESTING)
    add_subdirectory(cpp/tests)
endif()
