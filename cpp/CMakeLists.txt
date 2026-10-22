cmake_minimum_required(VERSION 3.15)
project(InfiniteDungeonAlgorithms LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

set(ALGO_SOURCES
    src/traversal.cpp
    src/pathfinding.cpp
    src/dungeon_generator.cpp
    src/knapsack.cpp
    src/backtracking_puzzle.cpp
)

# Static library
add_library(dungeon_algo STATIC ${ALGO_SOURCES})

# Shared library
add_library(dungeon_algo_shared SHARED ${ALGO_SOURCES})

# Test binary
add_executable(test_algorithms tests/test_algorithms.cpp)
target_link_libraries(test_algorithms PRIVATE dungeon_algo)

# Benchmark binary
add_executable(benchmark_runner benchmarks/benchmark_runner.cpp)
target_link_libraries(benchmark_runner PRIVATE dungeon_algo)
