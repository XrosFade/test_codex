# test_codex
work with codex, test repo

## SRPG Prototype (Rebuilt Baseline)

현재 코드는 다시 정리한 SRPG 베이스라인입니다.

### 포함 기능
- JSON 맵 로더 (`load_map_from_file`)
- 테스트용 단일 맵 시나리오 (`create_test_battle_state`)
- 이동 / 기본 공격
- 스킬 + 쿨다운 (MP 미사용)
- 자동 전투 루프 (`run_battle`)
- 기본 동작 점검 (`run_basic_behavior_check`)

### 실행
## SRPG Prototype (Python)

A minimal Japanese-style SRPG combat prototype is included in `src/srpg.py`.

### Features
- Grid-based movement with Manhattan distance.
- Speed-based deterministic turn order.
- Terrain system with move cost and defense bonus.
- Basic attack action with range checks.


### Run
```bash
python3 src/srpg.py
```

### 테스트
```bash
python3 -m pytest -q
```

### 매뉴얼
- `docs/map_loader_manual.md`
### Test
```bash
python3 -m pytest -q
```
