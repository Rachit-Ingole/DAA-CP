# 5. Backtracking — The Ancient Runic Vault (`U`)

## Slide: A Small Constraint-Satisfaction Problem

- 4 dials, each set to a rune 1–5.
- Constraints: neighbouring dials must differ, and the dials must sum to a target $T$.
- Press `S` to let the backtracking solver find a solution; it reports recursive calls, backtracks and time.

## Slide: Backtracking with Forward Pruning

```python
def backtrack(assignment):
    if len(assignment) == N:
        return sum(assignment) == T
    for rune in 1..M:
        assignment.append(rune)
        if is_valid_partial(assignment):   # prune early
            if backtrack(assignment):
                return True
        assignment.pop()                   # undo, try the next rune
    return False
```

Prune a partial assignment of length $k$ with sum $S_k$ and $R = N - k$ dials left if:
- $S_k + R > T$ (even all 1s overshoot),
- $S_k + R \cdot M < T$ (even all 5s fall short),
- the last two dials are equal.

## Slide: Always Solvable

- Generate a random *valid* assignment first, set $T$ to its sum, then run the solver to confirm before showing the puzzle.
- Worst case $O(M^N)$ = 625 leaves for 4 dials; pruning cuts whole subtrees.

## Speaker Notes

- Keep this section short — it is the smallest system. The interesting point is the bound-based pruning: checking whether the target is still reachable *before* recursing is what turns brute force into backtracking.
- If asked how this generalises: the same pattern (choose, check constraints, recurse, undo) solves Sudoku, N-Queens and graph colouring.
