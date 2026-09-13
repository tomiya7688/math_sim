add_executable(random_tree main.cpp)
target_compile_features(random_tree PRIVATE cxx_std_17)
target_include_directories(random_tree PRIVATE "${CMAKE_SOURCE_DIR}/cpp/include")

set_target_properties(random_tree PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
