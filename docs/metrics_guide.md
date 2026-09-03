# 日本語キーボード配列 評価尺度・計算仕様書 (NeoJ-A & NeoJ-B)

本ドキュメントは、日本語キーボード配列ベンチマークにおける2つの評価指標（NeoJ-A, NeoJ-B）および統合指標（Composite Index）の計算式・パラメータ定義を記述した技術仕様書です。

---

## 1. 全体構造

評価系は以下の2つの独立したモデル、およびそれらを統合する幾何平均指標で構成されます。

1. **NeoJ-A (打鍵エネルギー・物理仕事量モデル)**:
   スイッチ押下仕事、指の平面移動距離、段・列到達負荷、同指連続打鍵（SFB）ペナルティから算定される物理的負荷。
2. **NeoJ-B (運指流暢度・単語ボトルネックモデル)**:
   実用日本語語彙（5,000語以上）に対するシザーズ（段交差）、不自然な同時打鍵、DSFB（1打飛ばし同指）、運指ロール方向から算定される流暢性指標。
3. **Composite Index (総合評価指標)**:
   物理負荷と流暢度を均等基準で統合した幾何平均スコア。

---

## 2. NeoJ-A: 打鍵エネルギー・物理仕事量モデル

### パラメータ定義

#### (1) 指疲労係数 ($W_{\text{finger}}$)
各指の筋力・独立性に基づく重み係数：
- 中指 (Middle): $1.0$
- 人差指 (Index): $1.0$
- 薬指 (Ring): $1.15$
- 親指 (Thumb): $1.2$
- 小指 (Pinky): $1.3$

#### (2) 段到達ペナルティ ($P_{\text{row}}$)
ホーム段を基準とした手首・前腕の伸展/屈曲負荷：
- 数字段 (Row 0 / 最上段): $+1.5$ （手首の持ち上げ・前腕伸展）
- 上段 (Row 1): $+0.2$
- ホーム段 (Row 2): $0.0$
- 下段 (Row 3): $+0.25$
- 最下段・親指段 (Row 4): $0.0$

#### (3) 小指外側拡張ペナルティ ($P_{\text{lateral}}$)
ホーム列外側のキーを小指で打鍵する際の横方向ストレッチ負荷：
- 左小指外側 (`\``, `Tab`, `Caps`): $+0.6$
- 右小指外側1列目 (`[`, `'`, `-`): $+0.6$
- 右小指外側2列目 (`]`, `=`): $+1.2$
- 右小指外側3列目 (`\`): $+1.8$

#### (4) 平面移動負荷 ($E_{\text{travel}}$)
キートップ表面の水平移動距離（$d\text{ cm}$）：
$$E_{\text{travel}} = 0.1 \times d \times W_{\text{finger}}$$

#### (5) SFBペナルティ ($P_{\text{SFB}}$)
同一指による連続打鍵時の筋肉疲労加算：
$$P_{\text{SFB}} = 0.5 \times W_{\text{finger}}$$

### キーストロークあたりの仕事量算定式

各打鍵 $i$ における消費エネルギー $E_i$:
$$E_i = (1.0 + P_{\text{row}} + P_{\text{lateral}} + P_{\text{SFB}}) \times W_{\text{finger}} + E_{\text{travel}}$$

評価テキスト全体（文字数 $N_{\text{chars}}$）に対する1文字あたり仕事量：
$$\text{Effort/Char} = \frac{\sum_{i} E_i}{N_{\text{chars}}}$$

### 同時打鍵同期コスト（参考値）
同時打鍵1回につき $+0.3$ の同期コストを加算した値：
$$\text{SyncEffort/Char} = \frac{\sum_{i} E_i + 0.3 \times N_{\text{chords}}}{N_{\text{chars}}}$$

---

## 3. NeoJ-B: 運指流暢度・単語ボトルネックモデル

### 運指ペナルティ一覧

| 運指要素 | 条件・定義 | ペナルティ加算 |
| :--- | :--- | :---: |
| **重度シザーズ (Severe Scissors)** | 同手・隣接指で上下2段以上の段差があるキーの連続打鍵 | $+3.5 \times W_{\text{finger}}$ |
| **軽度シザーズ (Mild Scissors)** | 同手・隣接指で上下1段差の逆行運動 | $+1.4 \times W_{\text{finger}}$ |
| **無理な同時打鍵 (Awkward Chords)** | 同手での上下2段以上の異段キー同時押し、または非隣接指同時押し | $+3.5 \sim +5.0$ |
| **自然な同時打鍵 (Natural Chords)** | 親指シフト、同段隣接指、両手同時打鍵 | $+0.2 \sim +0.4$ |
| **同指連続打鍵 (SFB)** | 同一指による連続打鍵 | $+2.2 \sim +3.8$ |
| **1打飛ばし同指打鍵 (DSFB / Skipgram)** | 1打挟んだ直後の同一指再打鍵（同手挟み $+1.2$ / 逆手挟み $+0.8$） | $+0.8 \sim +1.2$ |
| **ロール運指 (In-roll / Out-roll)** | 外側→内側の流し打ち（In-roll: $+0.2$）/ 内側→外側（Out-roll: $+0.5$） | $+0.2 \sim +0.5$ |

### 単語難易度スコア $D(W)$ の算定式

各単語 $W$（打鍵数 $N_{\text{strokes}}$）に対し：
- $\text{TotalStrain}(W) = \sum \text{Penalties}$
- $\text{PeakStrain}(W) = \max(\text{TransitionStrain})$

$$D(W) = \frac{\text{TotalStrain}(W)}{N_{\text{strokes}}} + 0.5 \times \text{PeakStrain}(W)$$

### 単語分類基準
- **快適単語 (Smooth Words)**: $D(W) < 1.5$ かつ重度シザーズ・無理な同時打鍵・SFBが 0 回
- **難渋単語 (Awkward Words)**: $D(W) \ge 3.2$ または重度シザーズ・無理な同時打鍵が 1 回以上

### 流暢度スコア ($S_{\text{fluency}}$, 0-100 pt)
$$S_{\text{fluency}} = 0.5 \times \text{SmoothWords\%} + 0.5 \times (100 - \text{AwkwardWords\%})$$

---

## 4. Composite Index (総合評価スコア)

物理的仕事量の少なさ（省エネルギー性）と、運指流暢度スコアを幾何平均で統合します。

### サブスコアの正規化 (0-100 pt)

1. **純粋物理スコア ($S_{\text{pure}}$)**:
   基準上限 $1.0\text{ Effort/Char}$ (100点) 〜 基準下限 $3.0\text{ Effort/Char}$ (0点)
   $$S_{\text{pure}} = \text{clamp}\left( 100 \times \left(1 - \frac{\text{Effort/Char} - 1.0}{3.0 - 1.0}\right), 0, 100 \right)$$

2. **同期考慮物理スコア ($S_{\text{sync}}$)**:
   $$S_{\text{sync}} = \text{clamp}\left( 100 \times \left(1 - \frac{\text{SyncEffort/Char} - 1.0}{3.0 - 1.0}\right), 0, 100 \right)$$

3. **運指流暢度スコア ($S_{\text{fluency}}$)**:
   上記 NeoJ-B の算出値 (0-100 pt)

### 総合スコア ($S_{\text{composite}}$) の算定式

$$S_{\text{composite}} = \sqrt[3]{S_{\text{pure}} \times S_{\text{sync}} \times S_{\text{fluency}}}$$
