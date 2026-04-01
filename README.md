# test_codex
work with codex, test repo

## SRPG Prototype (Python)

A minimal Japanese-style SRPG combat prototype is included in `src/srpg.py`.

### Features
- Grid-based movement with Manhattan distance.
- Speed-based deterministic turn order.
- Terrain system with move cost and defense bonus.
- Basic attack action with range checks.
- Simple AI for enemy/player auto-turn simulation.

### Run
```bash
python3 src/srpg.py
```

### Test
```bash
python3 -m pytest -q
```
