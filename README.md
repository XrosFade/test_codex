# test_codex
work with codex, test repo

## SRPG Prototype (Python)

A minimal Japanese-style SRPG combat prototype is included in `src/srpg.py`.

### Features
- Grid-based movement with Manhattan distance.
- Speed-based deterministic turn order.
- Terrain system with move cost and defense bonus.
- Basic attack action with range checks.
- Skill system with cooldowns (no MP).
- JSON map loader for terrain object types.
- Simple AI for enemy/player auto-turn simulation.
- Testable single map scenario via `create_test_battle_state()`.
- Core behavior self-check via `run_basic_behavior_check()`.

### Run
```bash
python3 src/srpg.py
```

### Test
```bash
python3 -m pytest -q
```

### Map loader manual
- See `docs/map_loader_manual.md` for map JSON format and usage.
