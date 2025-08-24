# GetCurCur - 환율 정보 CLI 도구

[![PyPI - Version](https://img.shields.io/pypi/v/getcurcur.svg)](https://pypi.org/project/getcurcur)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/getcurcur.svg)](https://pypi.org/project/getcurcur)

GetCurCur는 다양한 은행의 실시간 환율 정보를 확인할 수 있는 Python 기반 CLI 도구입니다.

## 특징

- 🏦 **다중 은행 지원**: 한국 은행들의 환율 정보 제공 (하나은행, 우리은행 등)
- 🌍 **확장 가능한 구조**: 새로운 은행 및 국가 추가 용이
- 🚀 **빠른 성능**: 캐싱 기능으로 반복 조회 시 빠른 응답
- 🎨 **다양한 출력 형식**: 테이블, JSON, CSV 형식 지원
- 💱 **환율 계산기**: 통화 간 변환 기능
- 🔧 **설정 가능**: 사용자 정의 설정 파일 지원

## 설치

### Homebrew를 통한 설치 (macOS/Linux)

```bash
brew tap passingbreeze-bonfire/cellar
brew install getcurcur
```

### pip를 통한 설치

```bash
pip install getcurcur
```

### 개발 환경 설치

```bash
git clone https://github.com/passingbreeze-bonfire/homebrew-cellar.git
cd homebrew-cellar/getcurcur
pip install -e .
```

## 사용법

### 기본 환율 조회

```bash
# 기본 은행(하나은행)의 환율 정보 표시
getcurcur show

# 특정 은행의 환율 정보 표시
getcurcur show -b woori
getcurcur show -b korea.hana  # 국가.은행 형식도 지원

# 특정 통화만 표시
getcurcur show -c USD
getcurcur show --currency EUR
```

### 출력 형식 변경

```bash
# JSON 형식으로 출력
getcurcur show -f json

# CSV 형식으로 출력
getcurcur show -f csv

# 캐시 비활성화하고 최신 데이터 가져오기
getcurcur show --no-cache
```

### 환율 계산

```bash
# 100 USD를 KRW로 변환
getcurcur convert 100 USD

# 50 EUR를 KRW로 변환 (팔 때 환율 기준)
getcurcur convert 50 EUR --type sell

# 다른 은행의 환율로 계산
getcurcur convert 100 USD -b woori
```

### 기타 명령어

```bash
# 사용 가능한 모든 Provider 목록 표시
getcurcur list-providers

# 캐시 삭제
getcurcur clear-cache

# Playwright 브라우저 설치 (최초 설치 시 필요)
getcurcur install-browsers

# 버전 확인
getcurcur --version

# 도움말
getcurcur --help
```

## 설정

설정 파일은 `~/.getcurcur/config.json`에 저장됩니다.

```json
{
  "default_provider": "korea.hana",
  "cache": {
    "enabled": true,
    "ttl_minutes": 30
  },
  "browser": {
    "headless": true,
    "timeout": 30000
  },
  "output": {
    "default_format": "table",
    "default_currency": null
  }
}
```

## 아키텍처

### 프로젝트 구조

```
getcurcur/
├── src/getcurcur/
│   ├── __init__.py
│   ├── main.py              # CLI 진입점
│   ├── config.py            # 설정 관리
│   ├── exceptions.py        # 커스텀 예외
│   └── providers/           # 환율 Provider들
│       ├── base.py          # 기본 Provider 클래스
│       └── korea/           # 한국 은행들
│           ├── hana.py      # 하나은행
│           └── woori.py     # 우리은행
└── tests/                   # 테스트 코드
```

### 주요 컴포넌트

1. **Provider 시스템**: 각 은행은 `ExchangeRateProvider`를 상속하여 구현
2. **캐싱 시스템**: 30분 TTL의 로컬 캐시로 반복 요청 최적화
3. **에러 처리**: 구조화된 예외 처리로 안정적인 동작
4. **CLI 프레임워크**: Typer를 사용한 직관적인 명령어 구조

## 새로운 Provider 추가하기

새로운 은행을 추가하려면 `ExchangeRateProvider`를 상속하여 구현하면 됩니다:

```python
from getcurcur.providers.base import ExchangeRateProvider

class NewBankProvider(ExchangeRateProvider):
    def get_provider_name(self) -> str:
        return "New Bank"
    
    def get_country(self) -> str:
        return "KR"
    
    def fetch_rates(self) -> List[Dict[str, str]]:
        # 웹 스크래핑 로직 구현
        pass
```

## 기술 스택

- **Python 3.9+**: 메인 언어
- **Typer**: CLI 프레임워크
- **Playwright**: 웹 스크래핑
- **BeautifulSoup4**: HTML 파싱
- **Rich**: 터미널 UI

## 개발

### 테스트 실행

```bash
pytest tests/
```

### 코드 품질 검사

```bash
# Type checking
mypy src/getcurcur

# Linting
ruff check src/
```

## 라이선스

MIT License - 자세한 내용은 [LICENSE.txt](LICENSE.txt) 파일을 참조하세요.

## 기여하기

기여는 언제나 환영합니다! PR을 보내주시거나 이슈를 등록해주세요.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 문의

- 이슈: [GitHub Issues](https://github.com/passingbreeze-bonfire/homebrew-cellar/issues)
- 이메일: jeongmin1237@gmail.com