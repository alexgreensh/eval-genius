<p align="center">
  <img src="assets/img/eval-genius.png" alt="Eval Genius, the star-cloaked measurement sage" width="280">
</p>

<h1 align="center">Eval Genius</h1>
<p align="center"><strong>AIシステムについて、感覚ではなく、防御できる答えを。</strong></p>

<p align="center">
  あらゆるAIコーディングエージェント向けのスキル。あなたにevalが<em>いつ</em>必要か、<br>
  それがどこに当てはまるか、どう構築するか、そして結果をどう読むかを教えます。
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

### 誰もが「evalが必要だ」と言う。でも*いつ*なのかを言う人はほとんどいない。

## 問題

<p align="center"><img src="assets/img/problem.png" alt="Eval Genius at a crossroads of floating paths, unsure which way the evals go" width="100%"></p>

Evalは急にどこにでもあるものになった。AIのトークも、ローンチの投稿も、採用のスレッドも、みなevalが必要だと言う。でも実際に取り組もうとして座ると、疑問が次々と湧いてくる。

プロンプトの微調整に本当にevalは必要なのか、それともやりすぎか? ビルドのどの時点で最初のevalを入れるべきか? 「evalハーネス」とは、`evals/`という名前のフォルダを超えて、具体的に何なのか? どの指標で、サンプルは何件で、ジャッジモデルは本当にカウントされるのか? そしてついに数字が出たとき、40個中34個は良いのか? 3ポイントの改善は本物なのか、それともノイズなのか? あるいは、実行が静かにクラッシュして、合格を報告しただけなのか?

これらを感覚で答えると、大多数のチームと同じ結果になる。誰も信じないベンチマーク、何も評価していないから1ヶ月ずっと緑のままのゲート、そして鋭い質問一つで崩れるREADMEの数字。

## Eval Geniusの紹介

<p align="center"><img src="assets/img/solution.png" alt="Eval Genius with a compass and a star-map, weighing results on a set of scales" width="100%"></p>

Eval Geniusは、その欠けていた判断力を、あなたのAIエージェントが*あなたと一緒に*実行するスキルとしてパッケージしたものです。計測エンジニアのように考えます。結果を見る前に「より良い」の意味を決め、可能な限りのチェックをプレーンなコードに落とし、クラッシュを合格ではなく*未測定*として扱い、数字を最後に信じます。

事前に読むべきコースではありません。あなたが今どこにいるかを平易な言葉で説明すると、それが次のステップを踏み出します。そのステップが「まだ必要ない」であれ、「これがゲートです、そしてなぜこの実行結果は信頼できないのか」であれ。

ツール非依存で、依存関係もありません。`SKILL.md`と数個の標準ライブラリPythonスクリプトだけで構成されています。Claude Code、スキルを読み込む任意のエージェント、あるいはターミナルから単独で動きます。

## 何を聞けるか

<p align="center"><img src="assets/img/ask.png" alt="Eval Genius working hands-on, pulling a star-map into a laptop" width="100%"></p>

実際の疑問を、あなたが今いる場所から答えます:

- *「チャットボットにevalは必要? それとも今はやりすぎ?」*
- *「evalって、ビルドのどこに入るの?」*
- *「40個中34個だったけど、これって良いの?」*
- *「この3ポイントの改善、本物? それともノイズ?」*
- *「LLMジャッジを人間のラベルに対してキャリブレーションして。」*

セットアップの儀式も、事前に覚えるべき語彙もありません。状況を説明すれば、次の一手が返ってきます。

## あなたのために何をするか

<p align="center"><img src="assets/img/what-it-does.png" alt="Eval Genius crossing floating platforms through a pass/fail gate toward the results" width="100%"></p>

道のり全体を歩み、その途中のどの時点でも、スタートを含めて、あなたと出会います:

- **evalが本当に必要かを判断し**、最初のプロトタイプから本番まで、あなたの段階にどの種類がふさわしいかを選びます。
- **evalを選びます:** 何を測るか、どの採点器か(コード優先、アサーションが効かない箇所でのみジャッジ)、どの指標か、サンプルは何件か、公開ベンチマークを採用するか独自に構築するか。
- **構築してゲートにします:** フィクスチャ、ランナー、スコアラー、レポーター、実行前に書かれた基準値、そしてPASS、FAIL、CANNOT-MEASUREのいずれかで終わるCIゲート。不一致の実行結果の比較は拒否します。
- **結果を一緒に読みます:** あなたが書いた基準値に対して、ノイズの範囲、項目ごとの差分、そして驚くような数字を信じる前のハーネスバグのチェックを含めて。
- **正直に記述します**、注意事項、階層付け、比較ルールを明示的に。
- **見栄えの良い嘘を生む近道を拒否します:** 事後の基準値の変更、ブレンドスコア、緑になるまで実行、キャリブレーションされていないジャッジ。

## 最も間違えやすい部分は、ちゃんと処理済み

<p align="center"><img src="assets/img/scripts.png" alt="Eval Genius at a desk with a checklist, a bell curve, and a judge-vs-human scale" width="100%"></p>

4つの標準ライブラリのスクリプトがスキルに同梱され、単独で動きます:

| Script | 何を解決するか |
|---|---|
| `check_gate.py` | 変更をベースラインに対して項目ごとに比較し、**0 PASS**、**1 FAIL**、**2 CANNOT-MEASURE** で終了するため、クラッシュが合格を装うことは絶対にない |
| `paired_bootstrap.py` | 差に信頼区間を与え、「改善した」が実際に意味を持つようにする |
| `judge_agreement.py` | LLMジャッジが人間のラベルとどれくらい一致するかを、採点を任せる前に測定する |
| `hash_fixture.py` | ゲートが要求する正規の `fixture_hash` を出力し、同じフィクスチャでの2回の実行が黙って食い違わずに比較できるようにする |

## インストール

Eval Genius は Claude Code プラグインです。マーケットプレースを一度追加すれば、あとはインストールするだけです:

```bash
# in Claude Code
/plugin marketplace add alexgreensh/eval-genius
/plugin install eval-genius@eval-genius
```

プレーンなスキルフォルダを使いたい、または別のエージェントを使いたい? スキルは `skills/eval-genius/` にあります。あなたのエージェントが探す場所にコピーしてください:

```bash
cp -R skills/eval-genius ~/.claude/skills/eval-genius
# Any other agent: point it at skills/eval-genius/SKILL.md
```

あとは平易な言葉で話しかけるだけです(*「チャットボットにevalは必要?」*、*「この差は本物?」*、*「ジャッジをキャリブレーションして」*)。スクリプトは単独でも動きます:

```bash
python3 skills/eval-genius/scripts/check_gate.py --baseline base.json --treatment treat.json
```

Windows では、Python がそのようにインストールされている場合、`python3` の代わりに `py -3` を使ってください。

## 背景の考え方に興味がありますか?

スキルの背景にある完全な方法論は、平易な言葉で書かれた一つのドキュメント **[METHODOLOGY.md](METHODOLOGY.md)** にあります。スキルを使うのに必要ありません。考えを知りたいときのためのものです。

---

<div align="center">

Built by **Alex Greenshpun**. 役に立ったなら、スターかシェアが他の人にも届く助けになります。

<a href="https://github.com/alexgreensh"><img src="https://img.shields.io/badge/GitHub-alexgreensh-181717?logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://alexgreenshpun.com"><img src="https://img.shields.io/badge/Website-alexgreenshpun.com-8A5CF6" alt="Website"></a>
<a href="https://x.com/alexgreensh"><img src="https://img.shields.io/badge/X-%40alexgreensh-000000?logo=x&logoColor=white" alt="X"></a>

**License:** [Apache 2.0](LICENSE)

</div>
