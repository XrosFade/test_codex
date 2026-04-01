# SRPG Map Loader Manual

`src/srpg.py`의 `load_map_from_file()`는 JSON 파일에서 `BattleMap`을 생성합니다.

## 필수 포맷

- `width`: 맵 가로 크기 (int)
- `height`: 맵 세로 크기 (int)
- `tile_types`: 심볼 -> 지형 속성
- `rows`: 문자열 배열 (`height`개, 각 문자열 길이는 `width`)

예시:
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

## tile_types 상세

- `name`: 지형 이름
- `move_cost`: 이동 비용
- `defense_bonus`: 방어 보너스

## 사용 예시
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

## 검증 규칙

다음 조건이면 `ValueError`를 발생시킵니다.

- `len(rows) != height`
- 행 길이가 `width`와 다름
- `rows`에 정의되지 않은 심볼이 포함됨
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
