add_executable(random_tree main.cpp)

set_target_properties(random_tree PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
