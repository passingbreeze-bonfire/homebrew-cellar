# GetCurCur - 환율 조회 CLI 도구

## 프로젝트 개요

GetCurCur는 다양한 은행의 실시간 환율 정보를 확인할 수 있는 Python 기반 CLI 도구입니다. Playwright를 활용한 웹 스크래핑과 Typer CLI 프레임워크를 통해 사용자 친화적인 환율 조회 서비스를 제공합니다.

## 🎯 프로젝트 목표

- **다중 은행 지원**: 한국 및 해외 은행들의 환율 정보 제공
- **확장 가능한 구조**: Provider 패턴으로 새로운 은행 쉽게 추가 가능
- **사용자 친화적**: 직관적인 CLI 인터페이스와 다양한 출력 형식
- **성능 최적화**: 캐싱 및 효율적인 웹 스크래핑
- **안정성**: 견고한 에러 처리 및 테스트 커버리지

## 🏗️ 아키텍처

### 핵심 컴포넌트

1. **Provider 시스템** (`src/getcurcur/providers/`)
   - `ExchangeRateProvider`: 기본 추상 클래스
   - 국가별 서브디렉토리 (예: `korea/`)
   - 각 은행별 구현체

2. **CLI 인터페이스** (`src/getcurcur/main.py`)
   - Typer 기반 명령어 구조
   - Rich를 활용한 터미널 UI

3. **설정 관리** (`src/getcurcur/config.py`)
   - JSON 기반 사용자 설정
   - 캐시 및 브라우저 옵션

4. **예외 처리** (`src/getcurcur/exceptions.py`)
   - 구조화된 커스텀 예외

## 🛠️ 기술 스택

- **언어**: Python 3.9+
- **CLI 프레임워크**: Typer + Rich
- **웹 스크래핑**: Playwright
- **HTML 파싱**: BeautifulSoup4
- **빌드 도구**: Hatch
- **테스트**: pytest
- **품질 관리**: ruff, mypy
- **개발 도구**: mise

## 📁 프로젝트 구조

```
getcurcur/
├── .mise.toml              # 개발 환경 설정
├── pyproject.toml          # 프로젝트 메타데이터
├── README.md
├── tests/                  # 테스트 코드
│   ├── test_providers.py
│   └── test_cli.py
└── src/getcurcur/
    ├── __init__.py
    ├── __about__.py
    ├── main.py             # CLI 진입점
    ├── config.py           # 설정 관리
    ├── exceptions.py       # 커스텀 예외
    └── providers/          # 환율 Provider들
        ├── base.py         # 기본 Provider 클래스
        └── korea/          # 한국 은행들
            ├── hana.py     # 하나은행
            └── woori.py    # 우리은행
```

## 🚀 주요 기능

### 현재 지원 기능
- 하나은행, 우리은행 환율 조회
- 다양한 출력 형식 (테이블, JSON, CSV)
- 환율 계산기
- 캐싱 시스템
- 특정 통화 필터링

### 개발 예정 기능
- 추가 한국 은행 지원 (KB국민은행, 신한은행 등)
- 해외 은행 지원
- 환율 알람 기능
- 히스토리 조회

## 🔧 개발 환경 설정

```bash
# mise를 사용한 환경 설정
mise install
mise run setup
mise run browsers

# 개발 중 자주 사용할 명령어
mise run test      # 테스트 실행
mise run lint      # 린팅 검사
mise run format    # 코드 포맷팅
mise run demo      # 데모 실행
```

## 📊 현재 상태

- **개발 단계**: Beta
- **테스트 커버리지**: 향상 필요
- **문서화**: 기본 완료, 상세화 필요
- **CI/CD**: 미구축
- **코드 품질**: ruff, mypy 적용

## 🎯 우선순위 작업

1. **테스트 강화**: 단위 테스트 및 통합 테스트 완성
2. **새 Provider 추가**: KB국민은행, 신한은행 등
3. **에러 처리 개선**: 네트워크 오류, 파싱 오류 대응
4. **성능 최적화**: 병렬 처리, 캐시 전략 개선
5. **CI/CD 구축**: GitHub Actions를 통한 자동화

## 👥 Agent 역할 분담

### Backend Engineer (필수)
- Provider 시스템 확장
- 웹 스크래핑 로직 개선
- 성능 최적화
- 에러 처리 강화

### QA Engineer (권장)
- 테스트 프레임워크 완성
- 자동화된 테스트 구축
- CI/CD 파이프라인
- 코드 품질 자동화

### Technical Writer (선택)
- 상세 사용자 가이드
- API 문서화
- 개발자 온보딩 문서
- Provider 추가 가이드

## 🔍 코드 품질 가이드라인

- **타입 힌트**: 모든 함수에 타입 어노테이션 적용
- **에러 처리**: 명시적인 예외 처리
- **테스트**: 모든 주요 기능에 테스트 코드
- **문서화**: docstring 및 README 유지
- **코드 스타일**: ruff 규칙 준수

## 📈 성능 목표

- **응답 시간**: 평균 3초 이내
- **메모리 사용량**: 50MB 이하
- **캐시 적중률**: 80% 이상
- **에러율**: 5% 이하

## 🔐 보안 고려사항

- 사용자 에이전트 로테이션
- 요청 빈도 제한
- 민감 정보 로깅 방지
- HTTPS 통신 강제