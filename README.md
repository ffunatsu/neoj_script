# neoj_script

日本語キーボード配列の物理負荷・運指流暢度を評価するためのベンチマークスクリプトです。

---

## 1. 概要

`data/keymaps/` ディレクトリにキーマップ定義ファイル（JSON形式）を配置して実行することで、対象配列の打鍵負荷、運指移動距離、同指連続率、ハサミ討ち等の流暢度指標および総合スコアを算出して出力します。

初期状態で標準的なサンプル（JISかな、QWERTYローマ字）が `data/keymaps/` に配置されています。

---

## 2. 必要要件

- Python 3.10 以上
- パッケージ管理ツール: [uv](https://github.com/astral-sh/uv) （または pip）

### 依存パッケージのインストール

```bash
uv sync
```

---

## 3. 使い方

1. `data/keymaps/` に評価したいキーマップ定義ファイル（`.json`）を配置します。
2. スクリプトを実行します。

```bash
# 全ての評価を実行（NeoJ-A 物理負荷・NeoJ-B 流暢度・単語診断・総合スコア）
uv run python main.py

# 単語診断テーブルを省略してサマリ表のみ表示
uv run python main.py --no-words

# NeoJ-A（物理負荷・Effort）のみ評価
uv run python main.py --mode a

# NeoJ-B（運指流暢度・Fluency）のみ評価
uv run python main.py --mode b
```

---

## 4. ドキュメント・サンプル一覧

- **[評価尺度・計算仕様書 (docs/metrics_guide.md)](docs/metrics_guide.md)**:
  NeoJ-A（物理仕事量モデル）、NeoJ-B（運指流暢度・単語ボトルネックモデル）、および幾何平均による Composite Index の算定式とパラメータ詳細仕様。
- **[キーマップJSON仕様書 (docs/keymap_format.md)](docs/keymap_format.md)**:
  キーマップ定義ファイルで利用可能なフィールド、定数（`behavior.type`, `shiftType`, `roles` 等）、およびマッピング記法（`inputMappings`, `lookupTable`, `keyRemap`）の完全な仕様。
- **[実行サンプル (examples/)](examples/README.md)**:
  QWERTYローマ字およびJISかなのキーマップJSONサンプルと実行出力例。

---

## 5. ベンチマーク指標の概要

### NeoJ-A: 物理仕事量指標 (Physical Workload)

- **打鍵負荷 (Effort/字)**: スイッチ押下仕事（指ごとの疲労係数）、平面移動距離、段到達（数字段等）・小指外側拡張ペナルティ、同指連続（SFB）ペナルティの総和。
- **打鍵数/字**: 評価テキスト（1,097文字の平仮名コーパス）の1文字あたりの平均物理打鍵数。
- **総移動距離 (cm)**: ホームポジションを基準とした指先の総移動距離。
- **SFB率 (%)**: 同一の指で連続して打鍵する割合。
- **交互打鍵率 (%)**: 左右の手が交互に打鍵される割合。

### NeoJ-B: 運指流暢度指標 (Fluency & Biomechanical Strain)

- **流暢度スコア (0-100 pt)**: 実用語彙コーパス（5,000語以上）に対するシザーズ（段交差）、不自然な同時打鍵、DSFB（1打飛ばし同指）の発生頻度から算出される運指の滑らかさ指標。
- **快適単語率 (%)**: 引っかかりや過度な負荷なく入力できる単語の割合。
- **ハサミ討ち率 (回/100語)**: 上段・下段の逆行運動など、骨格上負荷の高い運指の発生頻度。

### 総合スコア (Composite Score, 0-100 pt)

- 物理仕事量スコア（純粋・同期考慮）と運指流暢度スコアを幾何平均で統合した総合指標。
