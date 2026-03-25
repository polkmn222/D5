# Implementation Plan - Phase 165: Documentation, README, and Test Updates

This phase brings all documentation, README files, and the test runner in sync with the current functionality of D4.

## Objective
1.  **Documentation Update**: Synchronize all `.md` files in `.gemini/development/docs/` with Phase 164 progress.
2.  **README.md Update**: Refine `.gemini/development/ai_agent/README.md` and provide a clear overview in `.gemini/development/README.md`.
3.  **test.py Creation**: Provide a standard `test.py` as a unified entry point for pytest runs (since it is currently missing).
4.  **Unit Testing**: Ensure comprehensive unit test coverage for all CRM and AI Agent features.
5.  **Phase Tracking**: Follow the mandatory backup and artifact storage workflow.

## Proposed Changes

### Documentation (Target: `.gemini/development/docs/`)
- **`erd.md`**: 신규 오브젝트(`Contact`, `Opportunity`, `Product`, `Asset`, `Brand`, `Model`, `MessageTemplate`)의 필드 및 관계 기술.
- **`skill.md`**: AI Agent의 'inline form' 패턴, 'snapshot card' 피드백 방식, 멀티 셀렉션 방지 로직 문서화.
- **`architecture.md`**: 현재의 하위 앱 마운트 구조 및 추천(recommendation) 서비스 흐름 반영.
- **`spec.md`**: 성공 기준에 멀티 레코드 액션 핸들링 및 다국어 지원 확정 내역 추가.

### README.md
- **AI Agent README**: Phase 164에서 강화된 CRUD 기능 및 사용자 선택 피드백 로직 상세 기술.
- **Root README**: 전체 프로젝트 구조, `run_crm.sh` 실행법, 신규 `test.py` 사용법을 포함된 개발 가이드 작성.

### Test Runner (`test.py`)
- **`test.py` (ROOT)**: `pytest`를 편리하게 실행할 수 있는 유틸리티 스크립트.
    - `PYTHONPATH` 자동 설정.
    - 옵션 지원 (예: `--all`, `--ai`, `--crm`, `--unit`).
    - 매뉴얼 테스트 대신 유닛 테스트를 쉽고 명확하게 수행할 수 있는 진입점 제공.

### Backups
- `.gemini/development/backups/101_199/phase165/`: 실행 전 전체 코드베이스 스냅샷 저장.

## Verification Plan

### Automated Tests
- Run `test.py` to trigger the unit test suite.
- Verification focus: `pytest .gemini/development/test/unit`.

### Manual Verification
- **STRICTLY PROHIBITED**: No manual browser or script-based observation will be used; verification relies entirely on automated unit tests.
