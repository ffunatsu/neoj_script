# 評価指標の計算仕様 (NeoJ-A & NeoJ-B)

> [!Warning]
> Antigravity IDE の支援により作ったもので、AI生成によって作られたコードやドキュメントなので、利用には十分な注意が必要です。

## 1. 概要
物理的な打鍵仕事量を計算する **NeoJ-A** と、運指の滑らかさ・単語単位の引っかかりを評価する **NeoJ-B**、およびこれらを幾何平均で統合する **Composite Index** の計算仕様です。

---

## 2. NeoJ-A: 物理仕事量モデル

### パラメータ
- **指疲労係数 ( $W_{\text{finger}}$ )**: 中・人: 1.0, 薬: 1.15, 親: 1.2, 小: 1.3
- **段到達ペナルティ ( $P_{\text{row}}$ )**: 数字段(Row 0): +1.5, 上段(Row 1): +0.2, ホーム段(Row 2): 0.0, 下段(Row 3): +0.25, スペース段(Row 4): 0.0
- **小指外側ストレッチ ( $P_{\text{lateral}}$ )**: 左端(`\``, `Tab`等): +0.6, 右端1列目(`[`, `'`等): +0.6, 右端2列目(`]`, `=`): +1.2, 右端3列目(`\`): +1.8
- **平面移動負荷 ( $E_{\text{travel}}$ )**: $0.1 \times \text{移動距離(cm)} \times W_{\text{finger}}$
- **SFBペナルティ ( $P_{\text{SFB}}$ )**: $+0.5 \times W_{\text{finger}}$

### 計算式
各打鍵 $i$ の仕事量 $E_i$:
$$E_i = (1.0 + P_{\text{row}} + P_{\text{lateral}} + P_{\text{SFB}}) \times W_{\text{finger}} + E_{\text{travel}}$$

1文字あたりの消費仕事量:
$$\text{Effort/Char} = \frac{\sum E_i}{N_{\text{chars}}}$$

同時打鍵同期コスト（参考値、1回あたり +0.3）:
$$\text{SyncEffort/Char} = \frac{\sum E_i + 0.3 \times N_{\text{chords}}}{N_{\text{chars}}}$$

---

## 3. NeoJ-B: 運指流暢度・単語快適度モデル

### 運指ペナルティ一覧
- **重度シザーズ**: 同手・隣接指で2段以上離れたキーの連続打鍵（ $+3.5 \times W_{\text{finger}}$ ）
- **軽度シザーズ**: 同手・隣接指で1段差の逆行運動（ $+1.4 \times W_{\text{finger}}$ ）
- **無理な同時押し**: 同手で2段以上離れたキーの同時押し、または非隣接指同時押し（ $+3.5 \sim +5.0$ ）
- **自然な同時押し**: 親指シフト、同段隣接指、両手同時押し（ $+0.2 \sim +0.4$ ）
- **SFB (同指連続)**: $+2.2 \sim +3.8$
- **DSFB (1打飛ばし同指)**: 同手挟み $+1.2$ / 逆手挟み $+0.8$
- **ロール運指**: 外→内（In-roll: $+0.2$ ）/ 内→外（Out-roll: $+0.5$ ）

### 単語難易度 $D(W)$
各単語 $W$（打鍵数 $N_{\text{strokes}}$）に対し、ペナルティ総和 $\text{TotalStrain}(W)$ と最大瞬間負荷 $\text{PeakStrain}(W)$ から算出:
$$D(W) = \frac{\text{TotalStrain}(W)}{N_{\text{strokes}}} + 0.5 \times \text{PeakStrain}(W)$$

- **快適単語 (Smooth)**: $D(W) < 1.5$ かつ 重度シザーズ・無理な同時押し・SFB が 0 回
- **難渋単語 (Awkward)**: $D(W) \ge 3.2$ または 重度シザーズ・無理な同時押しが 1 回以上

### 流暢度スコア (0-100 pt)
$$S_{\text{fluency}} = 0.5 \times \text{SmoothWords\%} + 0.5 \times (100 - \text{AwkwardWords\%})$$

---

## 4. Composite Index (総合スコア)

物理仕事量スコアと流暢度スコアを幾何平均で統合します。

### サブスコアの正規化 (0-100 pt)
- **純粋物理スコア**:
  $$S_{\text{pure}} = \text{clamp}\left( 100 \times \left(1 - \frac{\text{Effort/Char} - 1.0}{3.0 - 1.0}\right), 0, 100 \right)$$
- **同期考慮物理スコア**:
  $$S_{\text{sync}} = \text{clamp}\left( 100 \times \left(1 - \frac{\text{SyncEffort/Char} - 1.0}{3.0 - 1.0}\right), 0, 100 \right)$$

### 総合スコア
$$S_{\text{composite}} = \sqrt[3]{S_{\text{pure}} \times S_{\text{sync}} \times S_{\text{fluency}}}$$
