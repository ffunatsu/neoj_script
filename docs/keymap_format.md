# キーマップJSONの仕様

> [!Warning]
> Antigravity IDE の支援により作ったもので、AI生成によって作られたコードやドキュメントなので、利用には十分な注意が必要です。

`data/keymaps/` に置くキーマップ定義ファイル（`.json`）の書き方です。

---

## 主なフィールド

| フィールド | 説明 |
| :--- | :--- |
| `name` | 配列の表示名（省略時はファイル名） |
| `behavior.type` | `"sequential"`（単打・順次打鍵）または `"simultaneous"` / `"chords"`（同時押し） |
| `shiftType` | `"sands"`（スペースシフト）または `"dual_thumb"`（親指シフト）等 |
| `roles` | `holder1`（左親指シフト / デフォルト: `' '`）、`holder2`（右親指シフト / デフォルト: `'　'`） |
| `inputMappings` | 順次打鍵・単打辞書（例: `{"a": "は", "d e": "ほ"}`） |
| `lookupTable` | 同時押し辞書（例: `{"j+k": "か", "shift+3": "ぁ"}`） |
| `keyRemap` | QWERTYキーの再配置辞書（ローマ字配列用、例: `{"w": "l", "e": "u"}`） |

---

## 記述例

### 1. 順次打鍵・プレシフト (月配列など)
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

### 2. 同時打鍵・親指シフト (薙刀式・JISかななど)
```json
{
  "name": "JISかな",
  "behavior": { "type": "sequential" },
  "inputMappings": {
    "3": "あ",
    "t[": "が"
  },
  "lookupTable": {
    "shift+3": "ぁ"
  }
}
```

### 3. ローマ字キー再配置 (大西配列など)
```json
{
  "name": "大西配列",
  "behavior": { "type": "sequential" },
  "keyRemap": {
    "q": "q", "w": "l", "e": "u", "r": "f", "t": "w",
    "y": "r", "u": "y", "i": "p", "o": ".", "p": "k"
  }
}
```

---

## 特殊キーのエイリアス
- `space`, `holder1`: 半角スペース（左親指）
- `holder2`: 全角スペース（右親指）
- `semicolon`: `;` / `colon`: `:` / `comma`: `,` / `dot`: `.` / `slash`: `/` / `quote`: `'`
- `minus`: `-` / `caret`: `^` / `backslash`: `\` / `bracketleft`: `[` / `bracketright`: `]`
