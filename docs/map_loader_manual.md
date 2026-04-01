# SRPG Map Loader Manual

`src/srpg.py`의 `load_map_from_file()`는 JSON 파일에서 `BattleMap`을 생성합니다.

## 필수 포맷

- `width`: 맵 가로 크기 (int)
- `height`: 맵 세로 크기 (int)
- `tile_types`: 심볼 -> 지형 속성
- `rows`: 문자열 배열 (`height`개, 각 문자열 길이는 `width`)

예시:

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
