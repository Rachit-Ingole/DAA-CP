#include "dungeon/knapsack.hpp"
#include <chrono>
#include <algorithm>
#include <numeric>

namespace dungeon {

KnapsackResult solve_knapsack_dp(const std::vector<KnapsackItem>& items, int capacity) {
    auto t0 = std::chrono::high_resolution_clock::now();
    int n = static_cast<int>(items.size());
    int cap = std::max(0, capacity);

    // dp[i][w]
    std::vector<std::vector<int>> dp(n + 1, std::vector<int>(cap + 1, 0));

    for (int i = 1; i <= n; ++i) {
        int w_i = items[i - 1].weight;
        int v_i = items[i - 1].value;
        for (int w = 0; w <= cap; ++w) {
            if (w_i <= w) {
                int val_with = dp[i - 1][w - w_i] + v_i;
                int val_without = dp[i - 1][w];
                dp[i][w] = std::max(val_with, val_without);
            } else {
                dp[i][w] = dp[i - 1][w];
            }
        }
    }

    // Backtrack to find items
    std::vector<KnapsackItem> selected;
    int w_remain = cap;
    for (int i = n; i >= 1; --i) {
        if (dp[i][w_remain] != dp[i - 1][w_remain]) {
            selected.push_back(items[i - 1]);
            w_remain -= items[i - 1].weight;
        }
    }
    std::reverse(selected.begin(), selected.end());

    int total_wt = 0;
    for (const auto& it : selected) {
        total_wt += it.weight;
    }

    auto t1 = std::chrono::high_resolution_clock::now();

    KnapsackResult result;
    result.selected_items = std::move(selected);
    result.total_weight = total_wt;
    result.total_value = dp[n][cap];
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    result.method_name = "Dynamic Programming (0/1)";
    return result;
}

KnapsackResult solve_knapsack_greedy(const std::vector<KnapsackItem>& items, int capacity) {
    auto t0 = std::chrono::high_resolution_clock::now();
    int cap = std::max(0, capacity);

    // Make an indexed copy to sort by ratio descending
    std::vector<KnapsackItem> sorted_items = items;
    std::sort(sorted_items.begin(), sorted_items.end(), [](const KnapsackItem& a, const KnapsackItem& b) {
        return a.ratio() > b.ratio();
    });

    std::vector<KnapsackItem> selected;
    int current_weight = 0;
    int current_value = 0;

    for (const auto& item : sorted_items) {
        if (current_weight + item.weight <= cap) {
            selected.push_back(item);
            current_weight += item.weight;
            current_value += item.value;
        }
    }

    auto t1 = std::chrono::high_resolution_clock::now();

    KnapsackResult result;
    result.selected_items = std::move(selected);
    result.total_weight = current_weight;
    result.total_value = current_value;
    result.execution_time_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    result.method_name = "Greedy (Value/Weight Ratio)";
    return result;
}

KnapsackComparison compare_knapsack(const std::vector<KnapsackItem>& items, int capacity) {
    KnapsackComparison comp;
    comp.dp_result = solve_knapsack_dp(items, capacity);
    comp.greedy_result = solve_knapsack_greedy(items, capacity);

    if (comp.dp_result.total_value > 0) {
        comp.optimality_gap_pct = (static_cast<double>(comp.dp_result.total_value - comp.greedy_result.total_value) / 
                                   comp.dp_result.total_value) * 100.0;
    } else {
        comp.optimality_gap_pct = 0.0;
    }

    if (comp.greedy_result.execution_time_ms > 0.0) {
        comp.speedup_greedy_over_dp = comp.dp_result.execution_time_ms / comp.greedy_result.execution_time_ms;
    } else {
        comp.speedup_greedy_over_dp = 1.0;
    }

    return comp;
}

} // namespace dungeon
