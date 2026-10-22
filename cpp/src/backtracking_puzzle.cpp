#include "dungeon/backtracking_puzzle.hpp"
#include <chrono>
#include <numeric>
#include <random>

namespace dungeon {

bool RunePuzzle::is_valid_partial(const std::vector<int>& assignment) const {
    int k = static_cast<int>(assignment.size());
    if (k == 0) return true;

    // Constraint 1: No two adjacent dials may share the same rune
    if (k >= 2 && assignment[k - 1] == assignment[k - 2]) {
        return false;
    }

    // Constraint 2: Sum bounds check (forward pruning)
    int curr_sum = 0;
    for (int v : assignment) curr_sum += v;
    int remaining = num_dials - k;

    if (curr_sum + remaining * 1 > target_sum) {
        return false;
    }
    if (curr_sum + remaining * max_rune < target_sum) {
        return false;
    }

    // Custom constraints
    for (const auto& rule : custom_constraints) {
        if (!rule(assignment, k, num_dials)) {
            return false;
        }
    }

    return true;
}

bool RunePuzzle::solve(bool find_all) {
    auto t0 = std::chrono::high_resolution_clock::now();
    recursive_calls = 0;
    backtracks = 0;
    all_solutions.clear();
    solution.reset();

    std::vector<int> current;

    std::function<bool()> backtrack_fn = [&]() -> bool {
        recursive_calls++;

        if (static_cast<int>(current.size()) == num_dials) {
            int total = 0;
            for (int v : current) total += v;
            if (total == target_sum) {
                all_solutions.push_back(current);
                return !find_all; // stop early if not find_all
            }
            return false;
        }

        for (int val = 1; val <= max_rune; ++val) {
            current.push_back(val);
            if (is_valid_partial(current)) {
                if (backtrack_fn()) {
                    return true;
                }
            }
            backtracks++;
            current.pop_back();
        }

        return false;
    };

    backtrack_fn();

    auto t1 = std::chrono::high_resolution_clock::now();
    execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

    if (!all_solutions.empty()) {
        solution = all_solutions.front();
        return true;
    }
    return false;
}

RunePuzzle generate_solvable_puzzle(int num_dials, int max_rune, unsigned int seed) {
    std::mt19937 rng(seed ? seed : 1337);

    // 1. Generate guaranteed valid assignment
    std::vector<int> valid_assignment;
    valid_assignment.reserve(num_dials);

    for (int i = 0; i < num_dials; ++i) {
        std::vector<int> options;
        for (int v = 1; v <= max_rune; ++v) {
            if (i == 0 || v != valid_assignment.back()) {
                options.push_back(v);
            }
        }
        std::uniform_int_distribution<size_t> pick(0, options.size() - 1);
        valid_assignment.push_back(options[pick(rng)]);
    }

    int target_sum = 0;
    for (int v : valid_assignment) target_sum += v;

    RunePuzzle puzzle(num_dials, max_rune, target_sum, seed);
    puzzle.solve(false);
    return puzzle;
}

} // namespace dungeon
