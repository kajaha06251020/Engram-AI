<div align="center">

# Engram-AI

### AI 에이전트를 위한 경험 기반 메모리 인프라

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)

**[English](../../README.md)** | **[日本語](README_ja.md)** | **[中文](README_zh.md)** | **한국어** | **[Español](README_es.md)**

---

*현재 AI 메모리는 텍스트를 저장합니다. Engram-AI는 **각인**을 만듭니다 — 에이전트가 "무엇을 했고" "무슨 일이 일어났는지"로부터 학습하는 인과 구조입니다.*

</div>

## Engram-AI란?

대부분의 AI 메모리 시스템은 **일기장**처럼 작동합니다 — 텍스트 사실만 저장합니다: *"사용자는 Python을 좋아함"*, *"API는 REST 사용"*. 하지만 진정한 학습은 사실 암기가 아닌 **경험**에서 나옵니다.

Engram-AI는 AI 에이전트에게 **경험적 기억**을 제공합니다. 에이전트가 *아는 것*이 아니라, *무엇을 했는지*, *무슨 일이 일어났는지*, 그리고 결과가 *좋았는지 나빴는지*를 저장합니다:

```
행동:     API 응답 필드에 Optional[str] 사용
상황:     REST API 응답 모델 설계
결과:     사용자가 거부 — "응답에 null 값 불필요"
감정가:   -0.8 (부정적 경험)
```

시간이 지나면서 이러한 경험은 **스킬**로 결정화됩니다 — 에이전트가 자신의 이력 패턴에서 학습한 일반화된 규칙입니다.

## 빠른 시작

### 설치

```bash
pip install engram-ai
```

### Python 라이브러리로 사용

```python
from engram_ai import Forge

forge = Forge()

# 경험 기록
forge.record(
    action="리스트 컴프리헨션으로 데이터 변환",
    context="1만 행 CSV 처리",
    outcome="빠르고 가독성 좋음, 사용자 승인",
    valence=0.9,
)

# 과거 경험 쿼리
result = forge.query("데이터 변환 접근법")

# 패턴을 스킬로 결정화
skills = forge.crystallize()

# 학습한 스킬로 에이전트 설정 진화
forge.evolve(config_path="./CLAUDE.md")
```

### Claude Code 연동 (권장)

```bash
pip install engram-ai
engram-ai setup
# 끝! 자동으로 경험을 기록하고 학습을 시작합니다
```

## 핵심 작업

| 작업 | 설명 |
|------|------|
| **Record (기록)** | 경험 저장 (행동 + 상황 + 결과 + 감정가) |
| **Query (검색)** | 관련 과거 경험을 "최선"과 "피해야 할 것"으로 분류하여 검색 |
| **Crystallize (결정화)** | 유사 경험을 클러스터링하고 LLM으로 스킬 패턴 추출 |
| **Evolve (진화)** | 학습한 스킬을 에이전트 설정 (CLAUDE.md)에 기록 |

## 기여하기

모든 분의 기여를 환영합니다! [기여 가이드](../../CONTRIBUTING.md)를 참조하세요.

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## 라이선스

Apache License 2.0 — 자세한 내용은 [LICENSE](../../LICENSE)를 참조하세요.
