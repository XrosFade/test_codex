"""Minimal Japanese-style SRPG prototype with map loading and skill cooldowns."""

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


PLAINS = Tile(name="Plains", move_cost=1, defense_bonus=0)
FOREST = Tile(name="Forest", move_cost=2, defense_bonus=2)


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
    attack_range: int
    position: Position
    skills: List[Skill] = field(default_factory=list)
    skill_cooldowns: Dict[str, int] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class BattleMap:
    width: int
    height: int
    default_tile: Tile = PLAINS
    terrain: Dict[Position, Tile] = field(default_factory=dict)

    def in_bounds(self, position: Position) -> bool:
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, position: Position) -> Tile:
        return self.terrain.get(position, self.default_tile)


@dataclass
class GameState:
    battle_map: BattleMap
    units: List[Unit]

    def living_units(self, team: Optional[str] = None) -> List[Unit]:
        alive = [unit for unit in self.units if unit.is_alive()]
        if team is None:
            return alive
        return [unit for unit in alive if unit.team == team]

    def winner(self) -> Optional[str]:
        teams = {unit.team for unit in self.living_units()}
        if len(teams) == 1:
            return next(iter(teams))
        return None

    def unit_at(self, position: Position) -> Optional[Unit]:
        for unit in self.living_units():
            if unit.position == position:
                return unit
        return None

    def turn_order(self) -> List[Unit]:
        return sorted(self.living_units(), key=lambda unit: (-unit.speed, unit.name))


@dataclass
class BasicBehaviorReport:
    map_check: bool
    movement_check: bool
    attack_check: bool
    skill_check: bool
    cooldown_check: bool
    turn_order_check: bool
    details: List[str]

    @property
    def passed(self) -> bool:
        return all(
            [
                self.map_check,
                self.movement_check,
                self.attack_check,
                self.skill_check,
                self.cooldown_check,
                self.turn_order_check,
            ]
        )


def load_map_from_file(map_path: str | Path) -> BattleMap:
    """Load a battle map from JSON.

    Required JSON keys:
    - width, height
    - tile_types: dict of symbol -> {name, move_cost, defense_bonus}
    - rows: list[str] length == height, each row length == width
    """
    payload = json.loads(Path(map_path).read_text())

    width = int(payload["width"])
    height = int(payload["height"])
    rows: List[str] = payload["rows"]
    tile_types: Dict[str, Dict[str, int | str]] = payload["tile_types"]

    if len(rows) != height:
        raise ValueError("rows length must match height")
    if any(len(row) != width for row in rows):
        raise ValueError("every row length must match width")

    symbol_to_tile: Dict[str, Tile] = {}
    for symbol, tile_info in tile_types.items():
        symbol_to_tile[symbol] = Tile(
            name=str(tile_info["name"]),
            move_cost=int(tile_info.get("move_cost", 1)),
            defense_bonus=int(tile_info.get("defense_bonus", 0)),
        )

    terrain: Dict[Position, Tile] = {}
    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            if symbol not in symbol_to_tile:
                raise ValueError(f"Unknown tile symbol: {symbol}")
            tile = symbol_to_tile[symbol]
            if tile != PLAINS:
                terrain[(x, y)] = tile

    return BattleMap(width=width, height=height, terrain=terrain)


def create_test_battle_state(map_path: str | Path = "maps/default_map.json") -> GameState:
    battle_map = load_map_from_file(map_path)
    power_strike = Skill(name="Power Strike", power=4, attack_range=1, cooldown_turns=2)
    arrow_rain = Skill(name="Arrow Rain", power=3, attack_range=2, cooldown_turns=2)

    units = [
        Unit(
            "Hero",
            "player",
            hp=24,
            max_hp=24,
            atk=9,
            defense=4,
            speed=8,
            move=3,
            attack_range=1,
            position=(1, 1),
            skills=[power_strike],
        ),
        Unit(
            "Archer",
            "player",
            hp=18,
            max_hp=18,
            atk=7,
            defense=2,
            speed=7,
            move=3,
            attack_range=2,
            position=(1, 2),
            skills=[arrow_rain],
        ),
        Unit(
            "Bandit",
            "enemy",
            hp=20,
            max_hp=20,
            atk=8,
            defense=3,
            speed=6,
            move=3,
            attack_range=1,
            position=(6, 5),
            skills=[Skill(name="Heavy Slash", power=3, attack_range=1, cooldown_turns=2)],
        ),
        Unit(
            "Raider",
            "enemy",
            hp=16,
            max_hp=16,
            atk=6,
            defense=2,
            speed=5,
            move=4,
            attack_range=1,
            position=(6, 6),
            skills=[],
        ),
    ]
    return GameState(battle_map=battle_map, units=units)


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reachable_positions(state: GameState, unit: Unit) -> List[Position]:
    candidates: List[Position] = []
    ux, uy = unit.position

    for x in range(state.battle_map.width):
        for y in range(state.battle_map.height):
            position = (x, y)
            if position == unit.position:
                continue
            if state.unit_at(position) is not None:
                continue
            distance = manhattan((ux, uy), position)
            tile_cost = state.battle_map.tile_at(position).move_cost
            if distance + tile_cost - 1 <= unit.move:
                candidates.append(position)

    return sorted(candidates)


def move_unit(state: GameState, unit: Unit, target: Position) -> bool:
    if target not in reachable_positions(state, unit):
        return False
    unit.position = target
    return True


def deal_damage(attacker: Unit, defender: Unit, defender_tile: Tile, extra_power: int = 0) -> int:
    raw = attacker.atk + extra_power - (defender.defense + defender_tile.defense_bonus)
    return max(1, raw)


def basic_attack(state: GameState, attacker: Unit, defender: Unit) -> bool:
    if not attacker.is_alive() or not defender.is_alive():
        return False

    distance = manhattan(attacker.position, defender.position)
    if distance > attacker.attack_range:
        return False

    damage = deal_damage(attacker, defender, state.battle_map.tile_at(defender.position))
    defender.hp = max(0, defender.hp - damage)
    return True


def tick_cooldowns(unit: Unit) -> None:
    for skill_name, remaining in list(unit.skill_cooldowns.items()):
        if remaining > 0:
            unit.skill_cooldowns[skill_name] = remaining - 1


def is_skill_ready(unit: Unit, skill: Skill) -> bool:
    return unit.skill_cooldowns.get(skill.name, 0) == 0


def use_skill(state: GameState, attacker: Unit, defender: Unit, skill: Skill) -> bool:
    if not attacker.is_alive() or not defender.is_alive():
        return False
    if not is_skill_ready(attacker, skill):
        return False

    distance = manhattan(attacker.position, defender.position)
    if distance > skill.attack_range:
        return False

    damage = deal_damage(
        attacker,
        defender,
        state.battle_map.tile_at(defender.position),
        extra_power=skill.power,
    )
    defender.hp = max(0, defender.hp - damage)
    attacker.skill_cooldowns[skill.name] = skill.cooldown_turns
    return True


def nearest_enemy(state: GameState, unit: Unit) -> Optional[Unit]:
    enemy_team = "enemy" if unit.team == "player" else "player"
    enemies = state.living_units(team=enemy_team)
    if not enemies:
        return None
    return min(enemies, key=lambda enemy: (manhattan(unit.position, enemy.position), enemy.hp, enemy.name))


def choose_ready_skill_in_range(attacker: Unit, target: Unit) -> Optional[Skill]:
    distance = manhattan(attacker.position, target.position)
    for skill in attacker.skills:
        if is_skill_ready(attacker, skill) and distance <= skill.attack_range:
            return skill
    return None


def perform_enemy_turn(state: GameState, enemy: Unit) -> str:
    tick_cooldowns(enemy)
    target = nearest_enemy(state, enemy)
    if target is None:
        return f"{enemy.name} has no targets."

    skill = choose_ready_skill_in_range(enemy, target)
    if skill and use_skill(state, enemy, target, skill):
        return f"{enemy.name} uses {skill.name} on {target.name}. {target.name} HP={target.hp}."

    if basic_attack(state, enemy, target):
        return f"{enemy.name} attacks {target.name}. {target.name} HP={target.hp}."

    options = reachable_positions(state, enemy)
    if options:
        best = min(options, key=lambda pos: manhattan(pos, target.position))
        move_unit(state, enemy, best)

        skill = choose_ready_skill_in_range(enemy, target)
        if skill and use_skill(state, enemy, target, skill):
            return (
                f"{enemy.name} moves to {enemy.position} and uses {skill.name} on {target.name}. "
                f"{target.name} HP={target.hp}."
            )
        if basic_attack(state, enemy, target):
            return (
                f"{enemy.name} moves to {enemy.position} and attacks {target.name}. "
                f"{target.name} HP={target.hp}."
            )
        return f"{enemy.name} moves to {enemy.position}."

    return f"{enemy.name} waits."


def perform_player_turn(state: GameState, unit: Unit) -> str:
    tick_cooldowns(unit)
    target = nearest_enemy(state, unit)
    if target is None:
        return f"{unit.name} has no targets."

    skill = choose_ready_skill_in_range(unit, target)
    if skill and use_skill(state, unit, target, skill):
        return f"{unit.name} uses {skill.name} on {target.name}. {target.name} HP={target.hp}."

    if basic_attack(state, unit, target):
        return f"{unit.name} attacks {target.name}. {target.name} HP={target.hp}."

    options = reachable_positions(state, unit)
    if options:
        best = min(options, key=lambda pos: manhattan(pos, target.position))
        move_unit(state, unit, best)

        skill = choose_ready_skill_in_range(unit, target)
        if skill and use_skill(state, unit, target, skill):
            return (
                f"{unit.name} moves to {unit.position} and uses {skill.name} on {target.name}. "
                f"{target.name} HP={target.hp}."
            )
        if basic_attack(state, unit, target):
            return (
                f"{unit.name} moves to {unit.position} and attacks {target.name}. "
                f"{target.name} HP={target.hp}."
            )
        return f"{unit.name} moves to {unit.position}."

    return f"{unit.name} waits."


def run_battle(max_rounds: int = 20, state: Optional[GameState] = None) -> Tuple[Optional[str], List[str]]:
    state = state or create_test_battle_state()
    log: List[str] = []

    for round_number in range(1, max_rounds + 1):
        order = state.turn_order()
        log.append(f"-- Round {round_number} --")

        for actor in order:
            if not actor.is_alive():
                continue
            if actor.team == "enemy":
                result = perform_enemy_turn(state, actor)
            else:
                result = perform_player_turn(state, actor)
            log.append(result)

            winner = state.winner()
            if winner is not None:
                log.append(f"Winner: {winner}")
                return winner, log

    return state.winner(), log


def run_basic_behavior_check() -> BasicBehaviorReport:
    """Validate map loading and core actions including skills/cooldowns."""
    state = create_test_battle_state()
    details: List[str] = []

    map_ok = (
        state.battle_map.width == 8
        and state.battle_map.height == 8
        and state.battle_map.tile_at((2, 2)).name == "Forest"
        and state.battle_map.tile_at((0, 0)).name == "Plains"
    )
    details.append("map_check=ok" if map_ok else "map_check=fail")

    order_names = [unit.name for unit in state.turn_order()]
    turn_order_ok = order_names[:2] == ["Hero", "Archer"]
    details.append(f"turn_order={order_names}")

    hero = next(unit for unit in state.units if unit.name == "Hero")
    enemy = next(unit for unit in state.units if unit.name == "Bandit")
    enemy.position = (3, 1)

    movement_candidates = reachable_positions(state, hero)
    movement_ok = (2, 1) in movement_candidates and move_unit(state, hero, (2, 1))
    details.append(f"movement_options={len(movement_candidates)}")

    before_hp = enemy.hp
    attack_ok = basic_attack(state, hero, enemy) and enemy.hp < before_hp
    details.append(f"basic_attack_before={before_hp}, after={enemy.hp}")

    skill = hero.skills[0]
    enemy.hp = enemy.max_hp
    hero.skill_cooldowns[skill.name] = 0
    skill_before = enemy.hp
    skill_ok = use_skill(state, hero, enemy, skill) and enemy.hp < skill_before
    on_cooldown_now = hero.skill_cooldowns.get(skill.name, 0) > 0
    tick_cooldowns(hero)
    cooldown_changed = hero.skill_cooldowns.get(skill.name, 0) < skill.cooldown_turns
    cooldown_ok = on_cooldown_now and cooldown_changed
    details.append(f"skill_attack_before={skill_before}, after={enemy.hp}, cooldown={hero.skill_cooldowns.get(skill.name, 0)}")

    return BasicBehaviorReport(
        map_check=map_ok,
        movement_check=movement_ok,
        attack_check=attack_ok,
        skill_check=skill_ok,
        cooldown_check=cooldown_ok,
        turn_order_check=turn_order_ok,
        details=details,
    )


if __name__ == "__main__":
    report = run_basic_behavior_check()
    print(f"Basic behavior check passed: {report.passed}")
    for detail in report.details:
        print(f"- {detail}")

    winner, battle_log = run_battle()
    for line in battle_log:
        print(line)
    print(f"Final winner: {winner or 'none'}")
