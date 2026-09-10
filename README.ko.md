<p align="center">
  <img src="assets/img/eval-genius.png" alt="Eval Genius, the star-cloaked measurement sage" width="280">
</p>

<h1 align="center">Eval Genius</h1>
<p align="center"><strong>AI 시스템에 대한 방어 가능한 답, 감이 아니라.</strong></p>

<p align="center">
  모든 AI 코딩 에이전트를 위한 스킬로, 평가(eval)가 <em>언제</em> 필요한지 알려주고,<br>
어디에 들어맞는지, 어떻게 만드는지, 그리고 나온 결과를 어떻게 읽는지 알려줍니다.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License: Apache 2.0"></a>
  <img src="https://img.shields.io/badge/works%20across-Claude%20Code%20·%20Codex%20·%20Cursor%20·%20any%20agent-8A5CF6" alt="Works across any agent">
  <img src="https://img.shields.io/badge/scripts-stdlib%20Python%20·%20zero%20deps-2ea44f" alt="Stdlib Python, zero dependencies">
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.es.md">Español</a> · <strong>한국어</strong> · <a href="README.ja.md">日本語</a>
</p>

---

### 모두가 "평가(eval)가 필요하다"고 말합니다. 하지만 *언제*인지 말하는 사람은 거의 없습니다.

## 문제

<p align="center"><img src="assets/img/problem.png" alt="Eval Genius at a crossroads of floating paths, unsure which way the evals go" width="100%"></p>

평가(eval)가 갑자기 어디에나 있습니다. 모든 AI 발표, 모든 런칭 포스트, 모든 채용 스레드가 필요하다고 말합니다. 그런데 막상 직접 하려고 앉으면 질문이 시작됩니다.

프롬프트 조정에 정말 평가가 필요할까, 아니면 과한 걸까? 빌드의 어느 시점에 첫 평가가 들어가야 할까? "평가 하네스"란 구체적으로 `evals/`라는 폴더 이외에 무엇일까? 어떤 메트릭, 몇 개의 예제, 판정 모델(judge model)도 카운트가 될까? 그리고 마침내 숫자가 나왔을 때, 40점 만점에 34점이 좋은 걸까? 3점 향상은 진짜일까, 아니면 노이즈일까? 아니면 그냥 실행이 조용히 크래시되고 통과를 보고한 걸까?

이런 질문을 감으로 답하면, 대부분의 팀이 가진 것과 똑같은 결과가 나옵니다. 아무도 믿지 않는 벤치마크, 아무것도 평가하지 않아서 한 달 내내 초록색이었던 게이트, 그리고 날카로운 질문 하나에도 버티지 못할 README 속의 숫자.

## Eval Genius를 만나보세요

<p align="center"><img src="assets/img/solution.png" alt="Eval Genius with a compass and a star-map, weighing results on a set of scales" width="100%"></p>

Eval Genius는 그 빠진 판단력을, AI 에이전트가 당신과 *함께* 실행하는 스킬로 포장한 것입니다. 측정 엔지니어처럼 생각합니다. 보기 전에 "더 나음"이 무엇을 의미하는지 먼저 정하고, 가능한 모든 검사는 평범한 코드로 밀어내고, 크래시를 통과가 아니라 *미측정*으로 취급하며, 숫자를 가장 마지막에 신뢰합니다.

먼저 읽어야 하는 강좌가 아닙니다. 평범한 말로 지금 어디에 있는지 설명하면, 그다음 단계를 밟아줍니다. 그 단계가 "아직 필요 없다"든지, "여기 게이트가 있다, 그리고 이 실행을 왜 신뢰할 수 없는지"든지요.

도구에 구애받지 않고 의존성도 없습니다. `SKILL.md`와 표준 라이브러리 Python 스크립트 몇 개입니다. Claude Code에서 실행되거나, 스킬을 불러오는 모든 에이전트에서 실행되거나, 터미널에서 단독으로 실행됩니다.

## 무엇을 물어볼 수 있나

<p align="center"><img src="assets/img/ask.png" alt="Eval Genius working hands-on, pulling a star-map into a laptop" width="100%"></p>

실제 질문, 실제 있는 곳에서 답합니다:

- *"챗봇에 평가(eval)가 필요할까, 아니면 지금은 과한 걸까?"*
- *"평가는 내 빌드에 어디에 들어가야 할까?"*
- *"40점 만점에 34점을 받았는데, 좋은 걸까?"*
- *"이 3점 향상이 진짜일까, 아니면 노이즈일까?"*
- *"내 LLM 판정자(judge)를 사람 라벨로 보정해줘."*

설정 의식도 없고, 먼저 배워야 할 어휘도 없습니다. 상황을 설명하면, 다음 수를 얻습니다.

## 당신을 위해 무엇을 하나

<p align="center"><img src="assets/img/what-it-does.png" alt="Eval Genius crossing floating platforms through a pass/fail gate toward the results" width="100%"></p>

전체 경로를 걸으며, 그 경로의 어느 지점에서든, 시작점을 포함해 당신을 만납니다:

- **평가가 필요한지부터 결정합니다**, 그리고 첫 프로토타입부터 프로덕션까지, 당신의 단계에 어떤 종류가 어울리는지.
- **평가를 고릅니다:** 무엇을 측정할지, 어떤 채점기(코드 우선, 어서션이 안 통하는 곳만 판정자)를, 어떤 메트릭을, 몇 개 예제를, 공개 벤치마크를 쓸지 직접 만들지.
- **만들고 게이트를 겁니다:** 픽스처, 러너, 스코어, 리포터, 실행 전에 쓴 기준, 그리고 PASS, FAIL, 또는 CANNOT-MEASURE로 끝나며 매칭되지 않는 실행 비교를 거부하는 CI 게이트.
- **결과를 함께 읽습니다:** 당신이 쓴 기준에 맞춰, 노이즈 범위, 항목별 diff, 그리고 놀라운 숫자를 믿기 전에 하네스 버그 검사까지.
- **정직하게 정리합니다,** 주의사항, 등급, 그리고 비교 규칙을 분명히 밝히며.
- **예쁜 거짓말을 만드는 지름길을 거부합니다:** 사후에 기준 옮기기, 혼합 점수, 초록이 될 때까지 실행, 그리고 아무도 보정하지 않은 판정자.

## 가장 틀리기 쉬운 부분, 처리됨

<p align="center"><img src="assets/img/scripts.png" alt="Eval Genius at a desk with a checklist, a bell curve, and a judge-vs-human scale" width="100%"></p>

세 개의 표준 라이브러리 스크립트가 스킬과 함께 제공되며 단독으로 실행됩니다:

| 스크립트 | 정해주는 것 |
|---|---|
| `check_gate.py` | 변경을 항목별로 베이스라인과 비교, **0 PASS**, **1 FAIL**, **2 CANNOT-MEASURE**로 종료, 크래시가 통과로 위장하지 못하게 |
| `paired_bootstrap.py` | 차이에 신뢰 구간을 부여, "개선됐다"가 실제로 의미를 갖게 |
| `judge_agreement.py` | 판정자(judge)가 무엇이든 평가하게 두기 전에, LLM 판정자가 사람 라벨과 얼마나 일치하는지 측정 |

## 설치

스킬은 그냥 폴더입니다. 에이전트가 찾는 곳에 두세요:

```bash
# Claude Code
cp -R skill ~/.claude/skills/eval-genius

# 다른 에이전트: skill/SKILL.md를 가리키거나, skill/ 폴더를 스킬 경로에 추가
```

그런 다음 평범한 말로 이야기하세요 (*"내 챗봇에 평가가 필요할까?"*, *"이 델타 진짜야?"*, *"내 판정자 보정해줘"*). 스크립트는 단독으로도 실행됩니다:

```bash
python3 skill/scripts/check_gate.py --baseline base.json --treatment treat.json
```

## 추론이 궁금하신가?

스킬 뒤의 전체 방법론이, 평범한 언어로 된 한 문서에, **[METHODOLOGY.md](METHODOLOGY.md)**에 있습니다. 스킬을 쓰는 데 필요하지 않습니다. 생각을 보고 싶을 때를 위한 것입니다.

---

<div align="center">

**Alex Greenshpun**이 만들었습니다. 도움이 되셨다면, 스타나 공유가 다른 사람들이 찾게 도와줍니다.

<a href="https://github.com/alexgreensh"><img src="https://img.shields.io/badge/GitHub-alexgreensh-181717?logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://linkedin.com/in/alexgreensh"><img src="https://img.shields.io/badge/LinkedIn-alexgreensh-0A66C2?logo=linkedin&logoColor=white" alt="LinkedIn"></a>
<a href="https://x.com/alexgreensh"><img src="https://img.shields.io/badge/X-%40alexgreensh-000000?logo=x&logoColor=white" alt="X"></a>

**라이선스:** [Apache 2.0](LICENSE)

</div>
