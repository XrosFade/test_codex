from src.srpg import (
    BattleMap,
    FOREST,
    GameState,
    Skill,
    Unit,
    basic_attack,
    create_test_battle_state,
    deal_damage,
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


def test_map_loader_builds_battle_map_from_json():
    battle_map = load_map_from_file("maps/default_map.json")
    assert battle_map.width == 8
    assert battle_map.height == 8
    assert battle_map.tile_at((2, 2)).name == "Forest"
    assert battle_map.tile_at((0, 0)).name == "Plains"


def test_single_map_is_deterministic_and_testable():
    state = create_test_battle_state()
    assert state.battle_map.width == 8
    assert state.battle_map.height == 8
    assert state.battle_map.tile_at((2, 2)).name == "Forest"
    assert state.battle_map.tile_at((0, 0)).name == "Plains"
    assert len(state.living_units("player")) == 2
    assert len(state.living_units("enemy")) == 2


def test_skill_and_cooldown_work_without_mp():
    hero = Unit(
        "Hero",
        "player",
        hp=20,
        max_hp=20,
        atk=8,
        defense=3,
        speed=6,
        move=3,
        attack_range=1,
        position=(0, 0),
        skills=[Skill("Power Strike", power=4, attack_range=1, cooldown_turns=2)],
    )
    enemy = Unit("Enemy", "enemy", hp=20, max_hp=20, atk=6, defense=2, speed=4, move=3, attack_range=1, position=(1, 0))
    state = GameState(battle_map=BattleMap(width=4, height=4), units=[hero, enemy])

    skill = hero.skills[0]
    before_hp = enemy.hp
    assert use_skill(state, hero, enemy, skill)
    assert enemy.hp < before_hp
    assert hero.skill_cooldowns[skill.name] == 2

    assert not use_skill(state, hero, enemy, skill)
    tick_cooldowns(hero)
    tick_cooldowns(hero)
    assert hero.skill_cooldowns[skill.name] == 0
    assert use_skill(state, hero, enemy, skill)


def test_basic_behavior_check_verifies_core_actions():
    report = run_basic_behavior_check()
    assert report.map_check
    assert report.turn_order_check
    assert report.movement_check
    assert report.attack_check
    assert report.skill_check
    assert report.cooldown_check
    assert report.passed


def test_run_battle_ends_with_winner_or_timeout():
    winner, log = run_battle(max_rounds=30)
    assert log
    assert winner in {"player", "enemy", None}
