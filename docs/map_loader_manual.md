# SRPG Map Loader Manual

`src/srpg.py` includes `load_map_from_file()` to construct a `BattleMap` from JSON.

## 1) JSON format

A map file must include:

- `width`: map width (integer)
- `height`: map height (integer)
- `tile_types`: symbol-to-tile definition map
- `rows`: list of strings (exactly `height` lines, each line length `width`)

Example:

```json
{
  "width": 8,
  "height": 8,
  "tile_types": {
    "P": {"name": "Plains", "move_cost": 1, "defense_bonus": 0},
    "F": {"name": "Forest", "move_cost": 2, "defense_bonus": 2}
  },
  "rows": [
    "PPPPPPPP",
    "PPFFPPPP",
    "PPFFPPPP",
    "PPPPPPPP",
    "PPPPPPPP",
    "PPPPPPPP",
    "PPPPPPPP",
    "PPPPPPPP"
  ]
}
```

## 2) Tile object fields

Each tile type supports:

- `name` (string): display name
- `move_cost` (int): movement cost used by `reachable_positions()`
- `defense_bonus` (int): defense bonus used in damage calculation

## 3) Loading usage

```python
from src.srpg import load_map_from_file, create_test_battle_state

battle_map = load_map_from_file("maps/default_map.json")
state = create_test_battle_state("maps/default_map.json")
```

## 4) Validation rules

`load_map_from_file()` raises `ValueError` when:

- `len(rows) != height`
- any row length differs from `width`
- any symbol in `rows` is undefined in `tile_types`

## 5) Workflow recommendation

1. Create a new map JSON in `maps/`.
2. Load it via `create_test_battle_state("maps/your_map.json")`.
3. Run `run_basic_behavior_check()` and/or `python3 -m pytest -q`.
4. Adjust terrain, unit placement, and balance.
