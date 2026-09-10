<p align="center">
  <img src="assets/img/eval-genius.png" alt="Eval Genius，披着星光的测量智者" width="280">
</p>

<h1 align="center">Eval Genius</h1>
<p align="center"><strong>关于你的 AI 系统的站得住脚的答案，而不是凭感觉。</strong></p>

<p align="center">
  一个面向任意 AI 编程 agent 的技能，告诉你<em>什么时候</em>需要 eval、<br>
  它该放在哪里、怎么搭建，以及怎么解读跑出来的结果。
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License: Apache 2.0"></a>
  <img src="https://img.shields.io/badge/works%20across-Claude%20Code%20·%20Codex%20·%20Cursor%20·%20any%20agent-8A5CF6" alt="Works across any agent">
  <img src="https://img.shields.io/badge/scripts-stdlib%20Python%20·%20zero%20deps-2ea44f" alt="Stdlib Python, zero dependencies">
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.es.md">Español</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a>
</p>

---

### 人人都说"你需要 eval。"几乎没人说*什么时候*。

## 问题所在

<p align="center"><img src="assets/img/problem.png" alt="Eval Genius 站在漂浮路径的十字路口前，不知 eval 该往哪走" width="100%"></p>

Eval 突然无处不在。每场 AI 演讲、每篇发布文章、每个招聘帖都说你需要它。可当你真正坐下来动手时，问题就来了。

改个 prompt 真的需要 eval 吗，还是小题大做？第一个 eval 该在构建的哪个阶段加进去？抛开一个叫 `evals/` 的文件夹不谈，"eval harness" 具体是什么？该用哪个指标、多少条样本、judge 模型到底算不算数？当终于跑出一个数字时，40 道对 34 道算好吗？3 分的提升是真的，还是噪声？又或者运行其实悄悄崩了，却报了个通过？

凭感觉回答这些问题，你得到的正是大多数团队的现状：一个没人信的基准测试，一个挂了一个月还是绿的关卡（因为它根本没在打分），以及 README 里一个经不起一句尖锐追问的数字。

## 认识 Eval Genius

<p align="center"><img src="assets/img/solution.png" alt="Eval Genius 拿着指南针和星图，在天平上权衡结果" width="100%"></p>

Eval Genius 就是那个缺失的判断力，被打包成你的 AI agent *和你一起*运行的技能。它像一个测量工程师那样思考：在看结果之前先定义"更好"意味着什么，把能下放到普通代码里的检查都下放，把崩溃当作*未测量*而非通过，最后才相信数字。

它不是一门你得先读完的课。你用大白话描述你处在什么阶段，它就走出下一步，无论那一步是"你现在还不需要"还是"这就是关卡，以及为什么这次运行不能信"。

它工具无关、零依赖：一个 `SKILL.md` 加几个标准库 Python 脚本。它能在 Claude Code 里跑，也能在任何加载技能的 agent 里跑，还能在你的终端里独立运行。

## 你可以问它什么

<p align="center"><img src="assets/img/ask.png" alt="Eval Genius 亲自动手，把一张星图拉进笔记本电脑" width="100%"></p>

真实的问题，从你实际所处的位置回答你：

- *"我的聊天机器人需要 eval 吗，还是现在有点小题大做？"*
- *"eval 到底该放在我构建流程的哪里？"*
- *"我跑了 40 道对 34 道，这算好吗？"*
- *"这 3 分的提升是真的，还是噪声？"*
- *"拿一些人工标注来校准我的 LLM judge。"*

没有上手仪式，没有你得先学的术语。描述情况，拿到下一步该怎么做。

## 它替你做什么

<p align="center"><img src="assets/img/what-it-does.png" alt="Eval Genius 穿过漂浮平台，经过一个通过/失败关卡走向结果" width="100%"></p>

它走完整条路径，并在路径上的任意一点与你相遇，包括起点：

- **判断你到底需不需要 eval**，以及在你当前阶段（从首个原型到生产）该用哪一种。
- **挑选 eval：**测什么、用哪种评分器（优先用代码，只在没有任何断言可用时才上 judge）、用哪个指标、多少条样本、采用公开基准还是自建。
- **搭建并设关卡：**fixture、runner、scorer、reporter，一条在运行前就写好的及格线，以及一个以 PASS、FAIL 或 CANNOT-MEASURE 结束的 CI 关卡，并拒绝比较不匹配的运行。
- **和你一起解读结果：**对照你写下的及格线，带噪声上下界、逐条 diff，并在相信任何出人意料的数字之前先做一次 harness 缺陷检查。
- **诚实地写出来，**带上 caveat、分层，以及把比较规则大声说清楚。
- **拒绝那些产出漂亮谎言的捷径：**事后挪及格线、混合打分、跑到变绿为止、以及从没校准过的 judge。

## 最容易搞砸的部分，已经替你处理好

<p align="center"><img src="assets/img/scripts.png" alt="Eval Genius 坐在桌前，旁边是一份清单、一条钟形曲线和一杆 judge 对人工的天平" width="100%"></p>

技能附带三个标准库脚本，可独立运行：

| 脚本 | 它解决的问题 |
|---|---|
| `check_gate.py` | 逐条把变更与基线对比；以 **0 PASS**、**1 FAIL**、**2 CANNOT-MEASURE** 退出，让崩溃永远无法伪装成通过 |
| `paired_bootstrap.py` | 给差异加上置信区间，让"它变好了"真正有意义 |
| `judge_agreement.py` | 在你让 LLM judge 打分之前，先测量它和人工标注的一致程度 |

## 安装

技能就是一个文件夹。放到你的 agent 查找技能的位置：

```bash
# Claude Code
cp -R skill ~/.claude/skills/eval-genius

# 其他任意 agent：把路径指向 skill/SKILL.md，或把 skill/ 文件夹加到它的技能路径里
```

然后用大白话跟它说话（*"我的聊天机器人需要 eval 吗？"*、*"这个 delta 是真的吗？"*、*"校准我的 judge"*）。脚本也能独立运行：

```bash
python3 skill/scripts/check_gate.py --baseline base.json --treatment treat.json
```

## 想了解背后的推理？

技能背后的完整方法，写成一份大白话文档，放在 **[METHODOLOGY.md](METHODOLOGY.md)**。你不需要它也能用这个技能；它只是在你好奇思路时备查。

---

<div align="center">

由 **Alex Greenshpun** 打造。如果它对你有帮助，点个 star 或分享一下，能帮更多人发现它。

<a href="https://github.com/alexgreensh"><img src="https://img.shields.io/badge/GitHub-alexgreensh-181717?logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://alexgreenshpun.com"><img src="https://img.shields.io/badge/Website-alexgreenshpun.com-8A5CF6" alt="Website"></a>
<a href="https://x.com/alexgreensh"><img src="https://img.shields.io/badge/X-%40alexgreensh-000000?logo=x&logoColor=white" alt="X"></a>

**License:** [Apache 2.0](LICENSE)

</div>
