add_executable(pathfinding_replanning main.cpp)
target_include_directories(pathfinding_replanning PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)
set_target_properties(pathfinding_replanning PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
