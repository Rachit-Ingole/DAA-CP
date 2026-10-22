"""
backtracking_puzzle.py
CS3101: Constraint-Satisfaction Backtracking
Implementation of an Ancient Runic Vault Puzzle with guaranteed solvability validation.
"""

import random
import time


class RunePuzzle:
    """
    Represents an ancient dungeon rune lock puzzle.
    A sequence of N dials, each dialed to a rune symbol from 1 to M.
    Constraints:
      1. No two adjacent dials may share the same rune (c[i] != c[i+1]).
      2. The total sum of runes on all dials must match a mystic target T.
      3. Specific pairwise relationship constraints (e.g., dial[0] < dial[-1]).
    """
    def __init__(self, num_dials=4, max_rune=5, target_sum=12, constraints=None, seed=None):
        self.num_dials = num_dials
        self.max_rune = max_rune
        self.target_sum = target_sum
        self.constraints = constraints or []  # List of functions (assignment) -> bool
        self.seed = seed
        self.solution = None
        self.all_solutions = []
        self.recursive_calls = 0
        self.backtracks = 0
        self.execution_time_ms = 0.0

    def is_valid_partial(self, assignment):
        """Validates constraints on a partial or complete assignment."""
        k = len(assignment)
        if k == 0:
            return True

        # Constraint 1: Adjacent dials must not be identical
        if k >= 2 and assignment[-1] == assignment[-2]:
            return False

        # Constraint 2: Sum bounds check (prune if already exceeds target or cannot reach target)
        curr_sum = sum(assignment)
        remaining_dials = self.num_dials - k
        if curr_sum + remaining_dials * 1 > self.target_sum:
            return False  # Will definitely exceed target sum
        if curr_sum + remaining_dials * self.max_rune < self.target_sum:
            return False  # Cannot possibly reach target sum

        # Custom constraints check
        for rule in self.constraints:
            if not rule(assignment, k, self.num_dials):
                return False

        return True

    def solve(self, find_all=False):
        """
        Solves the puzzle using recursive backtracking.
        Explores valid domain values, checks partial consistency, and backtracks.
        """
        t0 = time.perf_counter()
        self.recursive_calls = 0
        self.backtracks = 0
        self.all_solutions = []

        def backtrack(current_assignment):
            self.recursive_calls += 1

            if len(current_assignment) == self.num_dials:
                if sum(current_assignment) == self.target_sum:
                    self.all_solutions.append(list(current_assignment))
                    return not find_all  # Stop early if find_all is False
                return False

            for val in range(1, self.max_rune + 1):
                current_assignment.append(val)
                if self.is_valid_partial(current_assignment):
                    solved = backtrack(current_assignment)
                    if solved:
                        return True
                self.backtracks += 1
                current_assignment.pop()

            return False

        backtrack([])
        t1 = time.perf_counter()
        self.execution_time_ms = (t1 - t0) * 1000.0
        self.solution = self.all_solutions[0] if self.all_solutions else None
        return self.solution is not None


def generate_solvable_puzzle(num_dials=4, max_rune=5, seed=None):
    """
    Generates a guaranteed solvable puzzle by:
    1. Choosing a valid base assignment using an isolated RNG.
    2. Deriving the target sum directly from the valid assignment.
    3. Running the backtracking solver to verify solvability.
    """
    rng = random.Random(seed)
    # Pick valid random assignment
    assignment = []
    for i in range(num_dials):
        available = [r for r in range(1, max_rune + 1) if not assignment or r != assignment[-1]]
        assignment.append(rng.choice(available))

    target = sum(assignment)
    puzzle = RunePuzzle(num_dials=num_dials, max_rune=max_rune, target_sum=target, seed=seed)
    is_solved = puzzle.solve(find_all=False)
    assert is_solved, "Generated puzzle must be solvable"
    return puzzle
