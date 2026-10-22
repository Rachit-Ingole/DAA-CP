#ifndef DUNGEON_BACKTRACKING_PUZZLE_HPP
#define DUNGEON_BACKTRACKING_PUZZLE_HPP

#include <vector>
#include <optional>
#include <functional>

namespace dungeon {

class RunePuzzle {
public:
    int num_dials{4};
    int max_rune{5};
    int target_sum{12};
    std::vector<std::function<bool(const std::vector<int>&, int, int)>> custom_constraints;
    unsigned int seed{0};

    // Solution & Metrics
    std::optional<std::vector<int>> solution;
    std::vector<std::vector<int>> all_solutions;
    int recursive_calls{0};
    int backtracks{0};
    double execution_time_ms{0.0};

    RunePuzzle() = default;
    RunePuzzle(int dials, int max_r, int target, unsigned int s = 0)
        : num_dials(dials), max_rune(max_r), target_sum(target), seed(s) {}

    bool is_valid_partial(const std::vector<int>& assignment) const;
    bool solve(bool find_all = false);
};

RunePuzzle generate_solvable_puzzle(int num_dials = 4, int max_rune = 5, unsigned int seed = 0);

} // namespace dungeon

#endif // DUNGEON_BACKTRACKING_PUZZLE_HPP
