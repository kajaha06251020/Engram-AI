<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### AI 에이전트를 위한 경험 기반 메모리 인프라

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](../../LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![codecov](https://img.shields.io/codecov/c/github/kajaha06251020/Engram-AI?style=flat-square)](https://codecov.io/gh/kajaha06251020/Engram-AI)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](../../CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=flat-square)](https://github.com/kajaha06251020/Engram-AI/stargazers)
[![Discord](https://img.shields.io/badge/Discord-join%20chat-7289DA?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/hGAcEfKqgq)

**[English](../../README.md)** | **[日本語](README_ja.md)** | **[中文](README_zh.md)** | **한국어** | **[Español](README_es.md)**

---

*기존 AI 메모리는 텍스트를 저장합니다. Engram-AI는 **흔적**을 만듭니다 — 에이전트가 자신이 한 일과 그 결과로부터 학습할 수 있게 해주는 인과적 구조입니다.*

</div>

## Engram-AI란 무엇인가요?

대부분의 AI 메모리 시스템은 **일기장**처럼 작동합니다 — 텍스트 사실을 저장합니다: *"사용자는 Python을 선호한다"*, *"API는 REST를 사용한다"*. 하지만 진정한 학습은 사실 암기에서 오지 않습니다. 그것은 **경험**에서 옵니다.

Engram-AI는 AI 에이전트에게 **경험적 메모리**를 제공합니다. 에이전트가 *무엇을 아는지* 저장하는 대신, 에이전트가 *무엇을 했는지*, *무슨 일이 일어났는지*, 그리고 그 결과가 *좋았는지 나빴는지*를 저장합니다:

```
행동:   API 응답 필드에 Optional[str] 사용
맥락:   REST API 응답 모델 설계 중
결과:   사용자가 거부함 — "응답에 null 값 없음"
감정값: -0.8 (부정적 경험)
```

시간이 지남에 따라, 이 경험들은 스킬로 **결정화**됩니다 — 에이전트가 자신의 과거 기록에서 패턴을 학습하여 일반화된 규칙을 만들어냅니다:

```
스킬:    "API 응답 모델에서 Optional 타입 사용 지양"
신뢰도: 0.85
근거:   경험 5개 (부정적 3개, 긍정적 2개)
```

그런 다음 스킬은 에이전트 설정으로 **진화**하여 에이전트를 영구적으로 개선시킵니다:

```markdown
<!-- engram-ai:start -->
## Engram-AI: Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-ai:end -->
```

## 왜 Engram-AI인가요?

| 기능 | 전통적 메모리 (Mem0 등) | Engram-AI |
|------|------------------------|-----------|
| **저장 내용** | 텍스트 사실 ("사용자가 X를 좋아함") | 인과적 구조 (행동 → 맥락 → 결과) |
| **학습 방식** | 저장된 텍스트 검색 | 경험에서의 패턴 결정화 |
| **학습 신호** | 없음 | 경험별 감정값 (-1.0 ~ +1.0) |
| **에이전트 개선** | 수동 프롬프트 조정 | 설정으로의 자동 스킬 진화 |
| **메모리 모델** | 일기 항목 | 신경 엔그램 (경험의 흔적) |

## 빠른 시작

### 설치

```bash
pip install engram-ai
```

### Python 라이브러리로 사용

```python
from engram_ai import Forge

forge = Forge()

# Record an experience
forge.record(
    action="Used list comprehension for data transform",
    context="Processing CSV with 10k rows",
    outcome="Fast and readable, user approved",
    valence=0.9,
)

# Query past experiences
result = forge.query("data transformation approach")
print(result["best"])   # 긍정적 경험
print(result["avoid"])  # 부정적 경험

# Crystallize patterns into skills
skills = forge.crystallize()

# Evolve agent config with learned skills
forge.evolve(config_path="./CLAUDE.md")
```

### Claude Code와 함께 사용 (권장)

자동 경험 기록을 설정하는 단 하나의 명령어:

```bash
# Install and configure
pip install engram-ai
engram-ai setup

# That's it! Engram-AI now:
# 1. Records experiences via hooks (PostToolUse, UserPromptSubmit)
# 2. Exposes tools via MCP server (query, crystallize, evolve)
# 3. Detects outcome valence from your reactions (keyword + LLM)
```

설정 후, Claude Code 에이전트가 자동으로:
- 모든 도구 사용을 대기 중인 경험으로 **기록**합니다
- 사용자의 응답이 긍정적/부정적인지 **감지**합니다
- 누적된 경험에서 패턴을 **학습**합니다
- 학습된 스킬로 자체 CLAUDE.md를 **진화**시킵니다

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    Forge (Facade)                     │
├──────────┬──────────┬──────────────┬────────────────┤
│ Recorder │ Querier  │ Crystallizer │    Evolver     │
├──────────┴──────────┴──────────────┴────────────────┤
│                    EventBus                          │
├─────────────────┬───────────────────────────────────┤
│  Storage Layer  │          LLM Layer                │
│  (ChromaDB)     │     (Claude API)                  │
├─────────────────┴───────────────────────────────────┤
│              Adapters (Claude Code)                  │
└─────────────────────────────────────────────────────┘
```

**핵심 연산:**

| 연산 | 설명 |
|------|------|
| **Record** | 경험 저장 (행동 + 맥락 + 결과 + 감정값) |
| **Query** | 관련 과거 경험 검색, "best"와 "avoid"로 분류 |
| **Crystallize** | 유사한 경험을 클러스터링하고 LLM을 통해 스킬 패턴 추출 |
| **Evolve** | 학습된 스킬을 에이전트 설정(CLAUDE.md)에 기록 |

## CLI 참조

```bash
engram-ai setup          # Claude Code용 자동 설정
engram-ai status         # 경험/스킬 수 표시
engram-ai query "topic"  # 과거 경험 검색
engram-ai crystallize    # 경험에서 스킬 추출
engram-ai evolve         # 스킬을 CLAUDE.md에 기록
engram-ai serve          # MCP 서버 시작
engram-ai dashboard      # 웹 대시보드 실행 (기본값: http://127.0.0.1:3333)
```

## MCP 도구

MCP 서버로 실행 시, Engram-AI는 다음 도구들을 제공합니다:

| 도구 | 설명 |
|------|------|
| `engram_record` | 감정값과 함께 경험 기록 |
| `engram_query` | 과거 경험 검색 |
| `engram_crystallize` | 패턴에서 스킬 추출 |
| `engram_evolve` | 설정에 스킬 기록 |
| `engram_status` | 통계 표시 |

## 작동 방식

### 2단계 기록

```
PostToolUse Hook          UserPromptSubmit Hook
     │                           │
     ▼                           ▼
Record Pending ──────────► Complete with Valence
(action + context)         (outcome + valence detection)
     │                           │
     ▼                           ▼
pending.jsonl              ChromaDB Storage
```

### 감정값 감지 (단계별)

1. **키워드 매칭** (무료) — 일본어 및 영어의 긍정/부정 패턴 감지
2. **LLM 폴백** (API 호출) — 키워드가 일치하지 않을 때
3. **기본값 0.3** — 두 방법 모두 실패할 때 약한 긍정적 가정

### 결정화 파이프라인

```
Experiences ──► Cluster by similarity ──► LLM extracts pattern ──► Skill
                (ChromaDB cosine)         (per cluster)            (rule + confidence)
```

## 웹 대시보드

Engram-AI에는 경험, 스킬, 신경망 그래프를 시각화하기 위한 실시간 웹 대시보드가 내장되어 있습니다.

```bash
engram-ai dashboard --port 3333
```

**4개 페이지:**

| 페이지 | 설명 |
|--------|------|
| **Overview (개요)** | 통계 카드, 감정값 추이 차트, 미니 신경망 그래프, 최근 경험 |
| **Experiences (경험)** | 검색, 필터, 정렬 가능한 테이블과 행 확장 기능 |
| **Skills (스킬)** | 신뢰도 막대가 있는 카드 그리드, 결정화/진화 실행 버튼 |
| **Graph (그래프)** | 육각형 스킬 노드가 있는 힘 기반 신경망 그래프, 클릭으로 강조 표시 |

**기능:**
- WebSocket을 통한 실시간 업데이트 (새로운 경험/스킬이 즉시 표시됨)
- 커스텀 색상 팔레트의 다크 테마
- 의존성 없는 서빙 (패키지에 번들된 정적 Next.js 내보내기)
- 사용자가 Node.js를 설치할 필요 없음

## 로드맵

Engram-AI v0.1은 기반이 되는 버전입니다. 아키텍처는 다음과 같은 계획된 기능들을 지원합니다:

- [x] **Dashboard (대시보드)** — 경험/스킬 시각화를 위한 웹 UI
- [ ] **Emotion tagging (감정 태깅)** — 감정값을 넘어선 풍부한 감정 표현
- [ ] **Experience chains (경험 체인)** — 관련 경험들의 연결된 시퀀스
- [ ] **Forgetting curves (망각 곡선)** — 시간 가중 관련성 감쇠
- [ ] **Skill marketplace (스킬 마켓플레이스)** — 에이전트 간 학습된 스킬 공유
- [ ] **Cross-agent transfer (에이전트 간 전이)** — 에이전트 인스턴스 간 전이 학습
- [ ] **Multi-LLM support (다중 LLM 지원)** — OpenAI, 로컬 모델 등
- [ ] **Reward shaping policies (보상 형성 정책)** — 커스텀 감정값 전략
- [ ] **Hierarchical memory (계층적 메모리)** — 에피소드 → 스킬 → 메타 스킬 계층
- [ ] **Privacy controls (개인정보 보호 제어)** — 선택적 메모리, 사용자 제어 삭제

20개의 계획된 기능 전체는 [전체 로드맵](docs/specs/2026-03-17-engram-ai-v0.1-design.md)을 참조하세요.

## 기여하기

모든 분들의 기여를 환영합니다! 자세한 내용은 [기여 가이드](../../CONTRIBUTING.md)를 참조하세요.

**기여자를 위한 빠른 시작:**

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # Windows에서는 .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

시작하려면 [good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)를 확인해보세요!

## 커뮤니티

- [GitHub Discussions](https://github.com/kajaha06251020/Engram-AI/discussions) — 질문, 아이디어, 작업 공유
- [Discord](https://discord.gg/hGAcEfKqgq) — 실시간 채팅
- [Issues](https://github.com/kajaha06251020/Engram-AI/issues) — 버그 신고 및 기능 요청

## 스타 히스토리

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=kajaha06251020/Engram-AI&type=Date)](https://star-history.com/#kajaha06251020/Engram-AI&Date)

</div>

## 라이선스

Apache License 2.0 — 자세한 내용은 [LICENSE](../../LICENSE)를 참조하세요.

---

<div align="center">

**Engram-AI가 AI 에이전트의 경험 학습에 도움이 된다면, 스타를 눌러주세요!**

<a href="https://github.com/kajaha06251020/Engram-AI/stargazers">
  <img src="https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=social" alt="GitHub Stars"/>
</a>

</div>
