from src.srpg import (
    BattleMap,
    GameState,
    Skill,
    Unit,
    basic_attack,
    compute_damage,
    create_test_battle_state,
    load_map_from_file,
    manhattan,
    move_unit,
    reachable_positions,
    run_basic_behavior_check,
    run_battle,
    tick_cooldowns,
    use_skill,
)


def test_manhattan_distance():
    assert manhattan((0, 0), (3, 4)) == 7


def test_movement_and_basic_attack():
    battle_map = BattleMap(width=5, height=5)
    hero = Unit("Hero", "player", 20, 20, 8, 3, 6, 3, 1, (0, 0))
    enemy = Unit("Enemy", "enemy", 12, 12, 6, 2, 4, 3, 1, (3, 0))
    state = GameState(battle_map, [hero, enemy])

    options = reachable_positions(state, hero)
    assert (2, 0) in options
    assert move_unit(state, hero, (2, 0))
    assert basic_attack(state, hero, enemy)
    assert enemy.hp < enemy.max_hp


def test_map_loader_and_single_map_state():
    loaded = load_map_from_file("maps/default_map.json")
    assert loaded.width == 8
    assert loaded.height == 8
    assert loaded.tile_at((2, 2)).name == "Forest"

    state = create_test_battle_state()
    assert len(state.living_units("player")) == 2
    assert len(state.living_units("enemy")) == 2


def test_skill_and_cooldown_without_mp():
    power = Skill("Power Strike", power=4, attack_range=1, cooldown_turns=2)
    hero = Unit("Hero", "player", 20, 20, 8, 3, 6, 3, 1, (0, 0), skills=[power])
    enemy = Unit("Enemy", "enemy", 20, 20, 6, 2, 4, 3, 1, (1, 0))
    state = GameState(BattleMap(4, 4), [hero, enemy])

    before = enemy.hp
    assert use_skill(state, hero, enemy, power)
    assert enemy.hp < before
    assert hero.cooldowns[power.name] == 2

    assert not use_skill(state, hero, enemy, power)
    tick_cooldowns(hero)
    tick_cooldowns(hero)
    assert hero.cooldowns[power.name] == 0


def test_compute_damage_floor():
    attacker = Unit("A", "player", 10, 10, 3, 1, 5, 3, 1, (0, 0))
    defender = Unit("D", "enemy", 10, 10, 3, 999, 4, 3, 1, (1, 0))
    assert compute_damage(attacker, defender, BattleMap(2, 2).tile_at((1, 0))) == 1


def test_behavior_check_and_battle_loop():
    report = run_basic_behavior_check()
    assert report.passed

    winner, logs = run_battle(max_rounds=30)
    assert logs
    assert winner in {"player", "enemy", None}
