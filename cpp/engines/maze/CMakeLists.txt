add_executable(maze main.cpp)
target_include_directories(maze PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)
set_target_properties(maze PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
