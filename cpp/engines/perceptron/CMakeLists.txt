add_executable(perceptron main.cpp)
target_include_directories(perceptron PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)

set_target_properties(perceptron PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines"
)
