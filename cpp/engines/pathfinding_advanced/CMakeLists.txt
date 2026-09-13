add_executable(pathfinding_advanced main.cpp)
target_include_directories(pathfinding_advanced PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)
set_target_properties(pathfinding_advanced PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
