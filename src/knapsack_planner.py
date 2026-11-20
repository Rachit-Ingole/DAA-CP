"""
knapsack_planner.py
CS3101: 0/1 Knapsack loot planner  [K]

Runs on the player's *real* situation instead of a fixed demo list:
    items     = everything in the bag + loot lying nearby (the whole vault
                room when standing in a treasure vault)
    capacity  = carry capacity (18 + 2 x STR) - weight of equipped gear
                (- potions / scrolls, which are kept unless C is toggled)
    objective = maximise total gold value

Shows the Dynamic Programming answer next to the Greedy (value / weight)
answer, draws the DP table dp[i][w] with the cells visited while
reconstructing the optimal subset, and lets the player apply either plan:
pick up the chosen floor items and drop the bag items that didn't make it.
"""
import sys
from constant import *
import config
import game_text
import item as item_module
import relics
from algorithms.knapsack import KnapsackItem, solve_knapsack_dp, solve_knapsack_greedy

CONSUMABLES = ("red potion", "blue potion", "teleport scroll")
ROW_H = 30
_icon_cache = {}


def _icon(name, size=26):
    key = (name, size)
    if key not in _icon_cache:
        _icon_cache[key] = pygame.transform.smoothscale(config.SPRITE.entity_dict[name], (size, size))
    return _icon_cache[key]


def _nearby_loot(player):
    """Floor items the plan may include: the whole vault when inside it, else within 2 tiles."""
    vault = getattr(config.MAP_INFO, 'vault_room', None)
    in_vault = vault and vault[0] <= player.x <= vault[2] and vault[1] <= player.y <= vault[3]
    loot = []
    for e in config.GAME_DATA.item_data:
        if not e.item:
            continue
        if in_vault and vault[0] <= e.x <= vault[2] and vault[1] <= e.y <= vault[3]:
            loot.append(e)
        elif max(abs(e.x - player.x), abs(e.y - player.y)) <= 2 and config.MAP_INFO.tile_array[e.y][e.x].seen:
            loot.append(e)
    return loot, bool(in_vault)


class Plan:
    """The knapsack instance built from the current game state, plus both solutions."""

    def __init__(self, keep_consumables):
        player = config.PLAYER
        self.keep_consumables = keep_consumables
        self.capacity = item_module.carry_capacity(player)
        self.strength = player.creature.stat.strength
        self.equipped_weight = sum(e.item.weight for e in item_module.equipped_entities(player))

        bag = list(player.container.inventory)
        kept = [e for e in bag if keep_consumables and e.item.name in CONSUMABLES]
        self.kept_weight = sum(e.item.weight for e in kept)
        bag = [e for e in bag if e not in kept]
        loot, self.in_vault = _nearby_loot(player)

        self.free = max(0, self.capacity - self.equipped_weight - self.kept_weight)
        self.entries = [(e, "Bag") for e in bag] + [(e, "Floor") for e in loot]
        # item_id = index + 1 (KnapsackItem treats 0 as "no id")
        self.items = [KnapsackItem(e.item.name.title(), max(1, e.item.weight), max(0, e.item.value), item_id=i + 1)
                      for i, (e, _) in enumerate(self.entries)]
        self.dp = solve_knapsack_dp(self.items, self.free)
        self.greedy = solve_knapsack_greedy(self.items, self.free)
        self.dp_ids = {it.item_id for it in self.dp.selected_items}
        self.greedy_ids = {it.item_id for it in self.greedy.selected_items}

    def apply(self, chosen_ids):
        """
        Picks up chosen floor items and drops bag items that were not chosen.

        Returns:
            True if anything changed (so a turn passes)
        """
        player = config.PLAYER
        taken = dropped = 0
        for i, (e, where) in enumerate(self.entries):
            chosen = (i + 1) in chosen_ids
            if where == "Floor" and chosen:
                if e.item.pick_up(player, auto_equip=False):
                    taken += 1
            elif where == "Bag" and not chosen:
                e.item.drop_item(player)
                dropped += 1
        if taken or dropped:
            game_text.add_game_message_to_print(
                f"Plan applied: took {taken}, left {dropped}. Bag {item_module.carried_weight(player)}"
                f"/{self.capacity}", (150, 230, 255))
        return bool(taken or dropped)


def knapsack_planner_menu(redraw_game):
    """
    Opens the planner. redraw_game() draws the game underneath.

    Returns:
        True if a plan was applied (the caller should pass a turn)
    """
    keep_consumables = True
    plan = Plan(keep_consumables)
    dim = None

    while True:
        redraw_game()
        surface = config.SURFACE_MAIN
        if dim is None or dim.get_size() != surface.get_size():
            dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            dim.fill((10, 12, 20, 235))
        surface.blit(dim, (0, 0))
        _draw(surface, plan)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_k):
                    return False
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return plan.apply(plan.dp_ids)
                if event.key == pygame.K_g:
                    return plan.apply(plan.greedy_ids)
                if event.key == pygame.K_c:
                    keep_consumables = not keep_consumables
                    plan = Plan(keep_consumables)

        config.CLOCK.tick(FPS)
        pygame.display.flip()


# ============================================================================
# Drawing
# ============================================================================
def _t(surface, font, text, colour, pos, center=False):
    r = game_text.render_cached(font, text, True, colour)
    if center:
        pos = (pos[0] - r.get_width() // 2, pos[1])
    surface.blit(r, pos)
    return r


def _draw(surface, plan):
    sw, sh = surface.get_size()
    _t(surface, FONT_CONTROL_TEXT, "LOOT PLANNER  -  0/1 KNAPSACK  (DP vs GREEDY)", (245, 215, 115), (sw // 2, 14), True)
    kept = f" - kept consumables {plan.kept_weight}" if plan.keep_consumables else ""
    _t(surface, FONT_HUD_SMALL,
       f"Capacity W = {plan.capacity} (18 + 2 x STR {plan.strength}) - equipped {plan.equipped_weight}{kept}"
       f"  =  {plan.free} free", WHITE, (sw // 2, 44), True)
    where = "Treasure vault: every relic in the room is a candidate" if plan.in_vault \
        else "Candidates: your bag + loot within 2 tiles (stand in a vault for the full haul)"
    _t(surface, FONT_HUD_SMALL, where, (190, 190, 210), (sw // 2, 64), True)

    _draw_table(surface, plan, 16, 96, min(560, sw // 2 + 40))
    right_x = min(560, sw // 2 + 40) + 34
    bottom = _draw_dp_table(surface, plan, right_x, 96, sw - right_x - 16, sh // 2 - 40)
    _draw_comparison(surface, plan, right_x, bottom + 14, sw - right_x - 16)

    pygame.draw.line(surface, (60, 70, 100), (16, sh - 44), (sw - 16, sh - 44), 1)
    _t(surface, FONT_HUD_SMALL,
       f"ENTER take DP plan    G take greedy plan    C keep potions/scrolls: {'ON' if plan.keep_consumables else 'OFF'}"
       f"    ESC close", (240, 220, 140), (sw // 2, sh - 34), True)


def _draw_table(surface, plan, x, y, width):
    cols = [("", 0), ("Item", 32), ("Where", 170), ("W", 238), ("V", 280), ("V/W", 322), ("DP", 386), ("Greedy", 436)]
    for label, cx in cols:
        _t(surface, FONT_HUD_SMALL, label, (150, 190, 245), (x + cx, y))
    y += 22
    pygame.draw.line(surface, (60, 70, 100), (x, y - 2), (x + width, y - 2), 1)

    if not plan.entries:
        _t(surface, FONT_HUD_SMALL, "Nothing to plan: your bag is empty and there is no loot nearby.",
           LIGHT_GREY, (x, y + 8))
        return

    max_rows = max(1, (surface.get_height() - y - 70) // ROW_H)
    for i, (e, where) in enumerate(plan.entries[:max_rows]):
        iid = i + 1
        in_dp, in_gr = iid in plan.dp_ids, iid in plan.greedy_ids
        if in_dp != in_gr:
            pygame.draw.rect(surface, (60, 40, 30), (x - 4, y - 2, width, ROW_H - 2))
        surface.blit(_icon(e.item.name), (x, y))
        colour = (255, 215, 80) if relics.is_relic(e.item.name) else WHITE
        _t(surface, FONT_HUD_SMALL, e.item.name.title(), colour, (x + 32, y + 5))
        _t(surface, FONT_HUD_SMALL, where, LIGHT_GREY if where == "Bag" else (150, 230, 255), (x + 170, y + 5))
        it = plan.items[i]
        _t(surface, FONT_HUD_SMALL, str(it.weight), WHITE, (x + 238, y + 5))
        _t(surface, FONT_HUD_SMALL, str(it.value), WHITE, (x + 280, y + 5))
        _t(surface, FONT_HUD_SMALL, f"{it.ratio:.2f}", LIGHT_GREY, (x + 322, y + 5))
        _t(surface, FONT_HUD_SMALL, "take" if in_dp else "-", (110, 255, 130) if in_dp else (110, 110, 120), (x + 386, y + 5))
        _t(surface, FONT_HUD_SMALL, "take" if in_gr else "-", (255, 180, 80) if in_gr else (110, 110, 120), (x + 436, y + 5))
        y += ROW_H
    hidden = len(plan.entries) - max_rows
    if hidden > 0:
        _t(surface, FONT_HUD_SMALL, f"+ {hidden} more (included in the optimisation)", LIGHT_GREY, (x, y + 4))


def _draw_dp_table(surface, plan, x, y, width, height):
    """Heat map of dp[i][w] with the reconstruction path highlighted. Returns the bottom y."""
    dp = plan.dp.dp_table
    n = len(dp) - 1 if dp else 0
    cap = len(dp[0]) - 1 if dp else 0
    _t(surface, FONT_HUD_SMALL, f"DP table dp[i][w]:  {n + 1} x {cap + 1} = {(n + 1) * (cap + 1)} cells",
       (150, 190, 245), (x, y))
    y += 22
    if not dp or cap == 0 or n == 0:
        _t(surface, FONT_HUD_SMALL, "(empty - nothing to choose)", LIGHT_GREY, (x, y))
        return y + 20

    cell_w = max(3, min(18, (width - 30) // (cap + 1)))
    cell_h = max(3, min(18, (height - 40) // (n + 1)))
    gx, gy = x + 26, y + 16
    top = max(1, dp[n][cap])
    for i in range(n + 1):
        for w in range(cap + 1):
            f = dp[i][w] / top
            colour = (int(20 + 40 * f), int(30 + 150 * f), int(60 + 160 * f))
            surface.fill(colour, (gx + w * cell_w, gy + i * cell_h, cell_w - 1, cell_h - 1))
    for i, w, took in plan.dp.trace:
        colour = (110, 255, 130) if took else (255, 220, 90)
        pygame.draw.rect(surface, colour, (gx + w * cell_w - 1, gy + i * cell_h - 1, cell_w + 1, cell_h + 1), 2)
    # Answer cell
    pygame.draw.rect(surface, WHITE, (gx + cap * cell_w - 2, gy + n * cell_h - 2, cell_w + 3, cell_h + 3), 2)

    _t(surface, FONT_HUD_SMALL, "w ->", LIGHT_GREY, (gx, y - 2))
    _t(surface, FONT_HUD_SMALL, "i", LIGHT_GREY, (x + 8, gy))
    bottom = gy + (n + 1) * cell_h + 6
    pygame.draw.rect(surface, (110, 255, 130), (x, bottom + 4, 10, 10), 2)
    _t(surface, FONT_HUD_SMALL, "take item i", LIGHT_GREY, (x + 16, bottom))
    pygame.draw.rect(surface, (255, 220, 90), (x + 120, bottom + 4, 10, 10), 2)
    _t(surface, FONT_HUD_SMALL, "skip item i", LIGHT_GREY, (x + 136, bottom))
    return bottom + 22


def _draw_comparison(surface, plan, x, y, width):
    dp, gr = plan.dp, plan.greedy
    pygame.draw.rect(surface, (24, 34, 50), (x, y, width, 150))
    pygame.draw.rect(surface, (60, 90, 140), (x, y, width, 150), 1)
    px = x + 10
    _t(surface, FONT_HUD_SMALL, "Dynamic Programming   O(N x W)", (110, 255, 130), (px, y + 8))
    _t(surface, FONT_HUD_SMALL, f"value {dp.total_value}   weight {dp.total_weight}/{plan.free}   "
                                f"{dp.execution_time_ms:.3f} ms", WHITE, (px, y + 28))
    _t(surface, FONT_HUD_SMALL, "Greedy by value/weight   O(N log N)", (255, 180, 80), (px, y + 56))
    _t(surface, FONT_HUD_SMALL, f"value {gr.total_value}   weight {gr.total_weight}/{plan.free}   "
                                f"{gr.execution_time_ms:.3f} ms", WHITE, (px, y + 76))
    if dp.total_value == 0:
        verdict, colour = "Nothing worth taking", LIGHT_GREY
    elif gr.total_value == dp.total_value:
        verdict, colour = "Greedy found the optimum this time", (110, 255, 130)
    else:
        pct = 100.0 * gr.total_value / dp.total_value
        verdict, colour = f"Greedy loses {dp.total_value - gr.total_value} gold ({pct:.0f}% of optimal)", (255, 120, 100)
    _t(surface, FONT_HUD_SMALL, verdict, colour, (px, y + 110))
