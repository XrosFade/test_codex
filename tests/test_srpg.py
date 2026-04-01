from src.srpg import (
    BattleMap,
    FOREST,
    GameState,
    Unit,
    basic_attack,
    deal_damage,
    manhattan,
    move_unit,
    reachable_positions,
    run_battle,
)


def test_manhattan_distance():
    assert manhattan((0, 0), (3, 4)) == 7


def test_damage_accounts_for_terrain_defense():
    attacker = Unit("A", "player", 10, 10, atk=10, defense=2, speed=5, move=3, attack_range=1, position=(0, 0))
    defender = Unit("D", "enemy", 10, 10, atk=5, defense=3, speed=4, move=3, attack_range=1, position=(1, 0))
    assert deal_damage(attacker, defender, FOREST) == 5


def test_movement_and_attack_flow():
    battle_map = BattleMap(width=5, height=5)
    hero = Unit("Hero", "player", 20, 20, atk=8, defense=3, speed=6, move=3, attack_range=1, position=(0, 0))
    enemy = Unit("Enemy", "enemy", 12, 12, atk=6, defense=2, speed=4, move=3, attack_range=1, position=(3, 0))
    state = GameState(battle_map=battle_map, units=[hero, enemy])

    options = reachable_positions(state, hero)
    assert (2, 0) in options
    assert move_unit(state, hero, (2, 0))
    assert basic_attack(state, hero, enemy)
    assert enemy.hp < enemy.max_hp


def test_run_battle_ends_with_winner_or_timeout():
    winner, log = run_battle(max_rounds=30)
    assert log
    assert winner in {"player", "enemy", None}
