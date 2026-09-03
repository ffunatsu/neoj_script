# neoj_script

日本語キーボード配列の物理負荷・運指流暢度を評価するためのベンチマークスクリプトです。

> [!Warning]
> 以下は、過去にNeoJスコアとして、結果データも含めて別リポジトリで公開していたものを、スクリプトだけ整理して再公開しているものです。
>
> Antigravity IDE の支援により作ったもので、AI生成によって作られたコードやドキュメントなので、利用には十分な注意が必要です。
>
> 元リポジトリを非公開にしている理由は、外部データが多く含まれていたこと、ランキングなどが含まれていて一部語弊があったこと、AI生成部のチェックが追いついていなかったこと、ライセンスの確認が不十分だったことなどです。

## 必要要件
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (または pip)

```bash
uv sync
```

## 使い方
`data/keymaps/` にキーマップJSONを置いて実行します（初期状態でJISかなとQWERTYのサンプルが入っています）。

```bash
# 全ての評価を実行（物理負荷・流暢度・単語診断・総合スコア）
uv run python main.py

# 単語診断を出さずに一覧表だけ表示
uv run python main.py --no-words

# 物理負荷（Effort）のみ
uv run python main.py --mode a

# 流暢度（Fluency）のみ
uv run python main.py --mode b
```

## ドキュメント
- [評価指標の計算仕様 (docs/metrics_guide.md)](docs/metrics_guide.md)
- [キーマップJSONの仕様 (docs/keymap_format.md)](docs/keymap_format.md)
- [結果サンプル (examples/)](examples/README.md)

## 主な指標
- **打鍵負荷 (Effort/字)**: スイッチ押下、移動距離、段・列到達、SFBペナルティの合計。
- **打鍵数/字**: 1文字あたりの平均打鍵数（平仮名1,097文字のコーパス）。
- **総移動距離 (cm)**: ホームポジションからの指の移動距離。
- **SFB率 (%)**: 同じ指での連続打鍵率。
- **交互打鍵率 (%)**: 左右交互に打った割合。
- **流暢度スコア (0-100)**: シザーズ（段交差）、無理な同時押し、DSFB（1打飛ばし同指）の少なさ。
- **快適単語率 (%)**: 無理なく打てる単語の割合（5,000語コーパス）。
- **ハサミ討ち率 (回/100語)**: 上下段の逆行など負荷の高い運指の頻度。
- **総合スコア (0-100)**: 物理負荷と流暢度を幾何平均でまとめたスコア。

## ライセンス・クレジット
- プログラムコード: [AGPL-3.0](LICENSE-AGPL)
- キーマップJSON構造・キー変換の設計: [hechima](https://github.com/msonrm/hechima) (MIT License / Copyright (c) 2026 msonrm, [LICENSE_HECHIMA](LICENSE_HECHIMA))
- 詳細は [LICENSE.md](LICENSE.md) を参照してください。
