"""Minimal Japanese-style SRPG prototype.

This module implements a small, turn-based grid combat loop with:
- deterministic speed-based turn order
- movement range checks on a tile map
- basic attack actions with distance-based weapon range
- simple enemy AI for automatic turns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Position = Tuple[int, int]


@dataclass(frozen=True)
class Tile:
    name: str
    move_cost: int = 1
    defense_bonus: int = 0


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
    turn_index: int = 0

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


def deal_damage(attacker: Unit, defender: Unit, defender_tile: Tile) -> int:
    raw = attacker.atk - (defender.defense + defender_tile.defense_bonus)
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


def nearest_enemy(state: GameState, unit: Unit) -> Optional[Unit]:
    enemies = state.living_units(team="enemy" if unit.team == "player" else "player")
    if not enemies:
        return None
    return min(enemies, key=lambda enemy: (manhattan(unit.position, enemy.position), enemy.hp, enemy.name))


def perform_enemy_turn(state: GameState, enemy: Unit) -> str:
    target = nearest_enemy(state, enemy)
    if target is None:
        return f"{enemy.name} has no targets."

    if basic_attack(state, enemy, target):
        return f"{enemy.name} attacks {target.name}. {target.name} HP={target.hp}."

    options = reachable_positions(state, enemy)
    if options:
        best = min(options, key=lambda pos: manhattan(pos, target.position))
        move_unit(state, enemy, best)
        if basic_attack(state, enemy, target):
            return (
                f"{enemy.name} moves to {enemy.position} and attacks {target.name}. "
                f"{target.name} HP={target.hp}."
            )
        return f"{enemy.name} moves to {enemy.position}."

    return f"{enemy.name} waits."


def perform_player_turn(state: GameState, unit: Unit) -> str:
    target = nearest_enemy(state, unit)
    if target is None:
        return f"{unit.name} has no targets."

    if basic_attack(state, unit, target):
        return f"{unit.name} attacks {target.name}. {target.name} HP={target.hp}."

    options = reachable_positions(state, unit)
    if options:
        best = min(options, key=lambda pos: manhattan(pos, target.position))
        move_unit(state, unit, best)
        if basic_attack(state, unit, target):
            return (
                f"{unit.name} moves to {unit.position} and attacks {target.name}. "
                f"{target.name} HP={target.hp}."
            )
        return f"{unit.name} moves to {unit.position}."

    return f"{unit.name} waits."


def run_battle(max_rounds: int = 20) -> Tuple[Optional[str], List[str]]:
    battle_map = BattleMap(width=8, height=8, terrain={(3, 3): FOREST, (4, 3): FOREST})
    units = [
        Unit("Hero", "player", hp=24, max_hp=24, atk=9, defense=4, speed=8, move=3, attack_range=1, position=(1, 1)),
        Unit("Archer", "player", hp=18, max_hp=18, atk=7, defense=2, speed=7, move=3, attack_range=2, position=(1, 2)),
        Unit("Bandit", "enemy", hp=20, max_hp=20, atk=8, defense=3, speed=6, move=3, attack_range=1, position=(6, 5)),
        Unit("Raider", "enemy", hp=16, max_hp=16, atk=6, defense=2, speed=5, move=4, attack_range=1, position=(6, 6)),
    ]
    state = GameState(battle_map=battle_map, units=units)

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


if __name__ == "__main__":
    winner, battle_log = run_battle()
    for line in battle_log:
        print(line)
    print(f"Final winner: {winner or 'none'}")
