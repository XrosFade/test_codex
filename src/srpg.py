"""SRPG prototype rebuilt with a clean, test-first baseline.

Scope:
- JSON map loader
- deterministic single map scenario
- movement / basic attack
- skill + cooldown (no MP)
- lightweight auto-battle loop for regression checks
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

Position = Tuple[int, int]


@dataclass(frozen=True)
class Tile:
    name: str
    move_cost: int = 1
    defense_bonus: int = 0


@dataclass(frozen=True)
class Skill:
    name: str
    power: int
    attack_range: int
    cooldown_turns: int


PLAINS = Tile("Plains", move_cost=1, defense_bonus=0)


@dataclass
class Unit:
    name: str
    team: str
    hp: int
    max_hp: int
    atk: int
    defense: int
    speed: int
    move: int
    basic_range: int
    position: Position
    skills: List[Skill] = field(default_factory=list)
    cooldowns: Dict[str, int] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class BattleMap:
    width: int
    height: int
    terrain: Dict[Position, Tile] = field(default_factory=dict)

    def tile_at(self, pos: Position) -> Tile:
        return self.terrain.get(pos, PLAINS)

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height


@dataclass
class GameState:
    battle_map: BattleMap
    units: List[Unit]

    def living_units(self, team: Optional[str] = None) -> List[Unit]:
        alive = [u for u in self.units if u.is_alive()]
        if team is None:
            return alive
        return [u for u in alive if u.team == team]

    def unit_at(self, pos: Position) -> Optional[Unit]:
        for unit in self.living_units():
            if unit.position == pos:
                return unit
        return None

    def winner(self) -> Optional[str]:
        teams = {u.team for u in self.living_units()}
        return next(iter(teams)) if len(teams) == 1 else None

    def turn_order(self) -> List[Unit]:
        return sorted(self.living_units(), key=lambda u: (-u.speed, u.name))


@dataclass
class BasicBehaviorReport:
    map_ok: bool
    movement_ok: bool
    basic_attack_ok: bool
    skill_ok: bool
    cooldown_ok: bool
    turn_order_ok: bool
    details: List[str]

    @property
    def passed(self) -> bool:
        return (
            self.map_ok
            and self.movement_ok
            and self.basic_attack_ok
            and self.skill_ok
            and self.cooldown_ok
            and self.turn_order_ok
        )


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def load_map_from_file(path: str | Path) -> BattleMap:
    payload = json.loads(Path(path).read_text())
    width = int(payload["width"])
    height = int(payload["height"])
    rows: List[str] = payload["rows"]
    tile_types: Dict[str, Dict[str, int | str]] = payload["tile_types"]

    if len(rows) != height:
        raise ValueError("rows length must equal height")
    if any(len(row) != width for row in rows):
        raise ValueError("every row length must equal width")

    symbols: Dict[str, Tile] = {}
    for symbol, info in tile_types.items():
        symbols[symbol] = Tile(
            name=str(info["name"]),
            move_cost=int(info.get("move_cost", 1)),
            defense_bonus=int(info.get("defense_bonus", 0)),
        )

    terrain: Dict[Position, Tile] = {}
    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            tile = symbols.get(symbol)
            if tile is None:
                raise ValueError(f"unknown tile symbol: {symbol}")
            if tile != PLAINS:
                terrain[(x, y)] = tile

    return BattleMap(width=width, height=height, terrain=terrain)


def create_test_battle_state(map_path: str | Path = "maps/default_map.json") -> GameState:
    battle_map = load_map_from_file(map_path)

    hero_skill = Skill("Power Strike", power=4, attack_range=1, cooldown_turns=2)
    archer_skill = Skill("Arrow Rain", power=3, attack_range=2, cooldown_turns=2)
    enemy_skill = Skill("Heavy Slash", power=3, attack_range=1, cooldown_turns=2)

    units = [
        Unit("Hero", "player", 24, 24, 9, 4, 8, 3, 1, (1, 1), skills=[hero_skill]),
        Unit("Archer", "player", 18, 18, 7, 2, 7, 3, 2, (1, 2), skills=[archer_skill]),
        Unit("Bandit", "enemy", 20, 20, 8, 3, 6, 3, 1, (6, 5), skills=[enemy_skill]),
        Unit("Raider", "enemy", 16, 16, 6, 2, 5, 4, 1, (6, 6), skills=[]),
    ]
    return GameState(battle_map, units)


def reachable_positions(state: GameState, unit: Unit) -> List[Position]:
    positions: List[Position] = []
    ux, uy = unit.position
    for x in range(state.battle_map.width):
        for y in range(state.battle_map.height):
            pos = (x, y)
            if pos == unit.position or state.unit_at(pos) is not None:
                continue
            distance = manhattan((ux, uy), pos)
            tile_cost = state.battle_map.tile_at(pos).move_cost
            if distance + tile_cost - 1 <= unit.move:
                positions.append(pos)
    return sorted(positions)


def move_unit(state: GameState, unit: Unit, target: Position) -> bool:
    if target not in reachable_positions(state, unit):
        return False
    unit.position = target
    return True


def compute_damage(attacker: Unit, defender: Unit, defender_tile: Tile, extra_power: int = 0) -> int:
    raw = attacker.atk + extra_power - (defender.defense + defender_tile.defense_bonus)
    return max(1, raw)


def basic_attack(state: GameState, attacker: Unit, defender: Unit) -> bool:
    if not attacker.is_alive() or not defender.is_alive():
        return False
    if manhattan(attacker.position, defender.position) > attacker.basic_range:
        return False
    damage = compute_damage(attacker, defender, state.battle_map.tile_at(defender.position))
    defender.hp = max(0, defender.hp - damage)
    return True


def tick_cooldowns(unit: Unit) -> None:
    for name, remaining in list(unit.cooldowns.items()):
        unit.cooldowns[name] = max(0, remaining - 1)


def skill_ready(unit: Unit, skill: Skill) -> bool:
    return unit.cooldowns.get(skill.name, 0) == 0


def use_skill(state: GameState, attacker: Unit, defender: Unit, skill: Skill) -> bool:
    if not attacker.is_alive() or not defender.is_alive():
        return False
    if not skill_ready(attacker, skill):
        return False
    if manhattan(attacker.position, defender.position) > skill.attack_range:
        return False

    damage = compute_damage(
        attacker,
        defender,
        state.battle_map.tile_at(defender.position),
        extra_power=skill.power,
    )
    defender.hp = max(0, defender.hp - damage)
    attacker.cooldowns[skill.name] = skill.cooldown_turns
    return True


def nearest_enemy(state: GameState, unit: Unit) -> Optional[Unit]:
    enemy_team = "enemy" if unit.team == "player" else "player"
    enemies = state.living_units(enemy_team)
    if not enemies:
        return None
    return min(enemies, key=lambda e: (manhattan(unit.position, e.position), e.hp, e.name))


def select_ready_skill(attacker: Unit, target: Unit) -> Optional[Skill]:
    distance = manhattan(attacker.position, target.position)
    for skill in attacker.skills:
        if skill_ready(attacker, skill) and distance <= skill.attack_range:
            return skill
    return None


def auto_turn(state: GameState, unit: Unit) -> str:
    tick_cooldowns(unit)
    target = nearest_enemy(state, unit)
    if target is None:
        return f"{unit.name} has no targets."

    skill = select_ready_skill(unit, target)
    if skill and use_skill(state, unit, target, skill):
        return f"{unit.name} uses {skill.name} on {target.name}. {target.name} HP={target.hp}."

    if basic_attack(state, unit, target):
        return f"{unit.name} attacks {target.name}. {target.name} HP={target.hp}."

    options = reachable_positions(state, unit)
    if options:
        best = min(options, key=lambda p: manhattan(p, target.position))
        move_unit(state, unit, best)
        skill = select_ready_skill(unit, target)
        if skill and use_skill(state, unit, target, skill):
            return f"{unit.name} moves to {unit.position} and uses {skill.name} on {target.name}. {target.name} HP={target.hp}."
        if basic_attack(state, unit, target):
            return f"{unit.name} moves to {unit.position} and attacks {target.name}. {target.name} HP={target.hp}."
        return f"{unit.name} moves to {unit.position}."

    return f"{unit.name} waits."


def run_battle(max_rounds: int = 20, state: Optional[GameState] = None) -> Tuple[Optional[str], List[str]]:
    state = state or create_test_battle_state()
    log: List[str] = []

    for round_no in range(1, max_rounds + 1):
        log.append(f"-- Round {round_no} --")
        for unit in state.turn_order():
            if not unit.is_alive():
                continue
            log.append(auto_turn(state, unit))
            winner = state.winner()
            if winner is not None:
                log.append(f"Winner: {winner}")
                return winner, log

    return state.winner(), log


def run_basic_behavior_check() -> BasicBehaviorReport:
    state = create_test_battle_state()
    details: List[str] = []

    map_ok = (
        state.battle_map.width == 8
        and state.battle_map.height == 8
        and state.battle_map.tile_at((2, 2)).name == "Forest"
        and state.battle_map.tile_at((0, 0)).name == "Plains"
    )
    details.append(f"map_ok={map_ok}")

    order = [u.name for u in state.turn_order()]
    turn_order_ok = order[:2] == ["Hero", "Archer"]
    details.append(f"turn_order={order}")

    hero = next(u for u in state.units if u.name == "Hero")
    bandit = next(u for u in state.units if u.name == "Bandit")
    bandit.position = (3, 1)

    moves = reachable_positions(state, hero)
    movement_ok = (2, 1) in moves and move_unit(state, hero, (2, 1))
    details.append(f"movement_ok={movement_ok}, options={len(moves)}")

    before_basic = bandit.hp
    basic_attack_ok = basic_attack(state, hero, bandit) and bandit.hp < before_basic
    details.append(f"basic_attack_hp={before_basic}->{bandit.hp}")

    skill = hero.skills[0]
    bandit.hp = bandit.max_hp
    before_skill = bandit.hp
    skill_ok = use_skill(state, hero, bandit, skill) and bandit.hp < before_skill
    details.append(f"skill_hp={before_skill}->{bandit.hp}")

    cooldown_before_tick = hero.cooldowns[skill.name]
    tick_cooldowns(hero)
    cooldown_after_tick = hero.cooldowns[skill.name]
    cooldown_ok = cooldown_after_tick < cooldown_before_tick
    details.append(f"cooldown={cooldown_before_tick}->{cooldown_after_tick}")

    return BasicBehaviorReport(
        map_ok=map_ok,
        movement_ok=movement_ok,
        basic_attack_ok=basic_attack_ok,
        skill_ok=skill_ok,
        cooldown_ok=cooldown_ok,
        turn_order_ok=turn_order_ok,
        details=details,
    )


if __name__ == "__main__":
    report = run_basic_behavior_check()
    print(f"Basic behavior check passed: {report.passed}")
    for d in report.details:
        print(f"- {d}")

    winner, logs = run_battle()
    for line in logs:
        print(line)
    print(f"Final winner: {winner or 'none'}")
