add_executable(monte_carlo_integral main.cpp)
target_compile_features(monte_carlo_integral PRIVATE cxx_std_17)
target_include_directories(monte_carlo_integral PRIVATE "${CMAKE_SOURCE_DIR}/cpp/include")

set_target_properties(monte_carlo_integral PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
