#ifndef DUNGEON_KNAPSACK_HPP
#define DUNGEON_KNAPSACK_HPP

#include <string>
#include <vector>

namespace dungeon {

struct KnapsackItem {
    std::string name;
    int weight{0};
    int value{0};
    std::string item_id;

    KnapsackItem() = default;
    KnapsackItem(std::string name_, int weight_, int value_, std::string id_ = "")
        : name(std::move(name_)), weight(weight_), value(value_), item_id(id_.empty() ? name : std::move(id_)) {}

    double ratio() const {
        return weight > 0 ? static_cast<double>(value) / weight : 1e9;
    }
};

struct KnapsackResult {
    std::vector<KnapsackItem> selected_items;
    int total_weight{0};
    int total_value{0};
    double execution_time_ms{0.0};
    std::string method_name;
};

struct KnapsackComparison {
    KnapsackResult dp_result;
    KnapsackResult greedy_result;
    double optimality_gap_pct{0.0};
    double speedup_greedy_over_dp{1.0};
};

KnapsackResult solve_knapsack_dp(const std::vector<KnapsackItem>& items, int capacity);
KnapsackResult solve_knapsack_greedy(const std::vector<KnapsackItem>& items, int capacity);
KnapsackComparison compare_knapsack(const std::vector<KnapsackItem>& items, int capacity);

} // namespace dungeon

#endif // DUNGEON_KNAPSACK_HPP
