# キーマップ定義ファイル (JSON) 仕様書

`data/keymaps/` 配下に配置するキーマップ定義ファイル（`.json`）のフォーマットおよび設定可能な定数・フィールド一覧です。

---

## 1. 最上位構造 (Top-Level Fields)

| フィールド名 | 型 | 必須 | 説明 |
| :--- | :--- | :---: | :--- |
| `name` | 文字列 | 任意 | ベンチマーク結果に表示される配列名（未指定時はファイル名）。 |
| `behavior` | オブジェクト | 任意 | 打鍵挙動の定義。`type` および `config` を含みます。 |
| `shiftType` | 文字列 | 任意 | シフト方式の指定（`"sands"`, `"dual_thumb"` 等）。 |
| `roles` | オブジェクト | 任意 | シフトキー・修飾キーの役割定義（`holder1`, `holder2`）。 |
| `inputMappings` | オブジェクト | 任意 | 順次打鍵・単打・プレシフトの対応辞書。 |
| `lookupTable` | オブジェクト | 任意 | 同時打鍵（コード）の対応辞書。 |
| `keyRemap` / `layoutMapping` | オブジェクト | 任意 | QWERTY物理キーと論理文字の再配置マッピング（ローマ字配列用）。 |

---

## 2. 定数・値の仕様

### (1) `behavior.type` (打鍵方式)
- `"sequential"`: 順次打鍵方式（単打、前置シフト、後置シフト、ローマ字入力等）。
- `"simultaneous"` または `"chords"`: 同時打鍵方式（2キー同時押し、親指シフト同時押し等）。

### (2) `shiftType` (シフト方式)
- `"sands"`: Space and Shift（単一スペースキーによるシフト併用）。
- `"dual_thumb"`: 左右親指（スペース/無変換/変換）による親指シフト。

### (3) `roles` (シフトキーのバインド)
親指キーや拡張シフトキーを定義します。
- `holder1`: 左親指シフト（デフォルト: 半角スペース `' '`）
- `holder2`: 右親指シフト（デフォルト: 全角スペース `'　'`）

```json
"roles": {
  "holder1": { "keys": ["space"] },
  "holder2": { "keys": ["henkan"] }
}
```

---

## 3. マッピング形式の指定

### 形式 A: 順次打鍵 (`inputMappings`)
単打または連続した打鍵シーケンスをかなにマッピングします。キー間は半角スペースで区切るか、連続した文字列として記述します。

```json
{
  "name": "月配列 2-263式",
  "behavior": { "type": "sequential" },
  "inputMappings": {
    "a": "は",
    "d e": "ほ",
    "k f": "ぬ"
  }
}
```

### 形式 B: 同時打鍵 (`lookupTable`)
2つ以上のキーの同時押しを定義します。キー名は `+` で連結します。

```json
{
  "name": "薙刀式 v18",
  "behavior": {
    "type": "simultaneous",
    "config": {
      "lookupTable": {
        "j": "あ",
        "space+d": "に",
        "f+j": "が"
      }
    }
  }
}
```
※ `lookupTable` は `behavior.config.lookupTable` またはトップレベルの `"lookupTable"` のいずれにも記述可能です。

### 形式 C: キー再配置 (`keyRemap` または `layoutMapping`)
QWERTYキーの物理位置とアルファベット/記号の対応を変更するローマ字系配列向けの設定です。

```json
{
  "name": "大西配列",
  "behavior": { "type": "sequential" },
  "keyRemap": {
    "q": "q",
    "w": "l",
    "e": "u",
    "r": "f",
    "t": "w",
    "y": "r",
    "u": "y",
    "i": "p",
    "o": ".",
    "p": "k"
  }
}
```

---

## 4. 特殊キー名エイリアス一覧

JSON 内で記号やスペースを指定する際、以下のエイリアス文字列を使用できます：

| エイリアス名 | 対応する記号 / 役割 |
| :--- | :--- |
| `space`, `holder1` | 半角スペース `' '` (左親指シフト) |
| `holder2` | 全角スペース `'　'` (右親指シフト) |
| `semicolon` | `;` |
| `colon` | `:` |
| `comma` | `,` |
| `dot`, `period` | `.` |
| `slash` | `/` |
| `quote` | `'` |
| `minus` | `-` |
| `caret` | `^` |
| `backslash` | `\` |
| `bracketleft` | `[` |
| `bracketright` | `]` |
| `at` | `@` |
