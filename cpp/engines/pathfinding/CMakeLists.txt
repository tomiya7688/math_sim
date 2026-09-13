add_executable(pathfinding main.cpp)
target_include_directories(pathfinding PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)
target_compile_features(pathfinding PRIVATE cxx_std_17)
set_target_properties(pathfinding PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
