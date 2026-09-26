cmake_minimum_required(VERSION 3.20)
project(math_sim_engines LANGUAGES CXX)

include(CTest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(MATH_SIM_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

if(MATH_SIM_ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        add_compile_options(
            -fsanitize=address,undefined
            -fno-omit-frame-pointer
            -fno-sanitize-recover=all
        )
        add_link_options(
            -fsanitize=address,undefined
            -fno-sanitize-recover=all
        )
    else()
        message(FATAL_ERROR "MATH_SIM_ENABLE_SANITIZERS requires GCC or Clang")
    endif()
endif()

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
