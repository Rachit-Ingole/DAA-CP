"""
knapsack.py
CS3101: Dynamic Programming vs Greedy Heuristic
0/1 Knapsack Problem for Inventory and Equipment Weight Optimization.
"""

import time


class KnapsackItem:
    """Represents an item with weight and value attributes."""
    def __init__(self, name, weight, value, item_id=None):
        self.name = name
        self.weight = int(weight)
        self.value = int(value)
        self.item_id = item_id or name

    @property
    def ratio(self):
        return self.value / self.weight if self.weight > 0 else float('inf')

    def __repr__(self):
        return f"{self.name} (w={self.weight}, v={self.value})"


class KnapsackResult:
    """Encapsulates the solution from a Knapsack solver."""
    def __init__(self, selected_items=None, total_weight=0, total_value=0, 
                 execution_time_ms=0.0, method_name=""):
        self.selected_items = selected_items or []
        self.total_weight = total_weight
        self.total_value = total_value
        self.execution_time_ms = execution_time_ms
        self.method_name = method_name


def solve_knapsack_dp(items, capacity):
    """
    Solves 0/1 Knapsack using classic Dynamic Programming table.
    
    Recurrence:
        DP[i][w] = max(DP[i-1][w], DP[i-1][w - w_i] + v_i)   if w_i <= w
                 = DP[i-1][w]                                  otherwise

    Time Complexity: O(N * W) where N = number of items, W = capacity.
    Space Complexity: O(N * W) for the 2D reconstruction table.
    """
    t0 = time.perf_counter()
    n = len(items)
    cap = max(0, int(capacity))

    # Initialize (n + 1) x (cap + 1) DP table
    dp = [[0] * (cap + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        item = items[i - 1]
        w_i = item.weight
        v_i = item.value
        for w in range(cap + 1):
            if w_i <= w:
                val_with = dp[i - 1][w - w_i] + v_i
                val_without = dp[i - 1][w]
                dp[i][w] = val_with if val_with > val_without else val_without
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtrack to reconstruct the optimal item subset
    selected = []
    w_remain = cap
    for i in range(n, 0, -1):
        if dp[i][w_remain] != dp[i - 1][w_remain]:
            item = items[i - 1]
            selected.append(item)
            w_remain -= item.weight

    selected.reverse()
    total_val = dp[n][cap]
    total_wt = sum(it.weight for it in selected)
    t1 = time.perf_counter()

    return KnapsackResult(
        selected_items=selected,
        total_weight=total_wt,
        total_value=total_val,
        execution_time_ms=(t1 - t0) * 1000.0,
        method_name="Dynamic Programming (0/1)"
    )


def solve_knapsack_greedy(items, capacity):
    """
    Solves 0/1 Knapsack using a Greedy heuristic:
    Sorts items by value-to-weight ratio (v_i / w_i) in descending order,
    and greedily takes whole items until capacity is exhausted.

    Time Complexity: O(N log N) dominated by sorting.
    Space Complexity: O(N) auxiliary space.
    """
    t0 = time.perf_counter()
    cap = max(0, int(capacity))

    # Sort by ratio descending; tie-break on higher value
    sorted_items = sorted(items, key=lambda it: (it.ratio, it.value), reverse=True)

    selected = []
    curr_weight = 0
    curr_value = 0

    for item in sorted_items:
        if curr_weight + item.weight <= cap:
            selected.append(item)
            curr_weight += item.weight
            curr_value += item.value

    t1 = time.perf_counter()
    return KnapsackResult(
        selected_items=selected,
        total_weight=curr_weight,
        total_value=curr_value,
        execution_time_ms=(t1 - t0) * 1000.0,
        method_name="Greedy (Value-to-Weight Ratio)"
    )


def compare_knapsack(items, capacity):
    """
    Runs both Dynamic Programming and Greedy solvers on the same item set and capacity.
    Returns a comprehensive comparison dictionary including competitive ratio.
    """
    dp_res = solve_knapsack_dp(items, capacity)
    greedy_res = solve_knapsack_greedy(items, capacity)

    ratio = (greedy_res.total_value / dp_res.total_value) if dp_res.total_value > 0 else 1.0

    return {
        "capacity": capacity,
        "item_count": len(items),
        "dp_value": dp_res.total_value,
        "dp_weight": dp_res.total_weight,
        "dp_time_ms": dp_res.execution_time_ms,
        "dp_items": [it.name for it in dp_res.selected_items],
        "greedy_value": greedy_res.total_value,
        "greedy_weight": greedy_res.total_weight,
        "greedy_time_ms": greedy_res.execution_time_ms,
        "greedy_items": [it.name for it in greedy_res.selected_items],
        "greedy_competitive_ratio": ratio,
        "optimal_reached": dp_res.total_value == greedy_res.total_value
    }
