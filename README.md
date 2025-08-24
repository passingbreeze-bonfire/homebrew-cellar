# Passingbreeze-bonfire Cellar

🛠️ **CLI Tools Repository for passingbreeze-bonfire Organization**  
**passingbreeze의 CLI 도구 저장소**

> 이 저장소는 passingbreeze가 개발하는 모든 CLI 도구들을 관리하는 Homebrew tap입니다.  
> This repository serves as a Homebrew tap for all CLI tools developed by the passingbreeze.

---

## 📦 설치 방법 / Installation

### 방법 1: 직접 설치 / Direct Installation
```bash
brew install passingbreeze-bonfire/cellar/<패키지명>
# brew install passingbreeze-bonfire/cellar/<formula>
```

### 방법 2: Tap 추가 후 설치 / Tap then Install
```bash
# Tap 추가 / Add tap
brew tap passingbreeze-bonfire/cellar

# 패키지 설치 / Install package
brew install <패키지명>
# brew install <formula>
```

### 방법 3: Brewfile 사용 / Using Brewfile
```ruby
tap "passingbreeze-bonfire/cellar"
brew "<패키지명>"
# brew "<formula>"
```

---

## 📋 사용 가능한 CLI 도구 / Available CLI Tools

현재 이 저장소에서 제공하는 CLI 도구들:  
*Currently available CLI tools in this repository:*

> 🚧 **아직 패키지가 없습니다 / No packages available yet**  
> 새로운 CLI 도구가 추가되면 이 섹션이 업데이트됩니다.  
> *This section will be updated as new CLI tools are added.*

---

## 📚 문서 및 도움말 / Documentation & Help

### Homebrew 관련 / Homebrew Related
- `brew help` - Homebrew 도움말 / Homebrew help
- `man brew` - Homebrew 매뉴얼 페이지 / Homebrew manual page
- [Homebrew 공식 문서 / Official Documentation](https://docs.brew.sh)

### 패키지별 도움말 / Package-specific Help
각 CLI 도구의 자세한 사용법은 해당 도구의 `--help` 옵션을 사용하세요.  
*For detailed usage of each CLI tool, use the `--help` option with the respective tool.*

```bash
<패키지명> --help
# <formula> --help
```

---

## 🤝 기여하기 / Contributing

버그 리포트나 기능 제안이 있으시면 GitHub Issue를 작성해주시거나 각 CLI 도구의 개별 저장소에서 작업하고 pull request를 올려주세요.  
*For bug reports or feature requests, please write an issue on GitHub or submit a pull request to each CLI tool's individual repository.*

**passingbreeze-bonfire**: https://github.com/passingbreeze-bonfire

---

## 📄 라이선스 / License

각 CLI 도구는 개별적인 라이선스를 가질 수 있습니다.  
*Each CLI tool may have its own license.*

자세한 라이선스 정보는 각 패키지의 문서를 확인해 주세요.  
*Please check the individual package documentation for detailed license information.*
