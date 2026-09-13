add_executable(mlp main.cpp)
target_include_directories(mlp PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)
target_compile_features(mlp PRIVATE cxx_std_17)
set_target_properties(mlp PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/engines")
