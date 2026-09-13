cmake_minimum_required(VERSION 3.20)
project(monte_carlo_pi LANGUAGES CXX)

add_executable(monte_carlo_pi main.cpp)
target_compile_features(monte_carlo_pi PRIVATE cxx_std_17)

set_target_properties(monte_carlo_pi PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
