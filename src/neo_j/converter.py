"""
Keystroke Converter for Japanese Keyboard Layouts.
Generates:
1. Pure physical keystrokes (data/generated/*.source.txt)
2. Chord-annotated keystrokes (data/chords_generated/*.source.txt) with (k1+k2) notation.
"""
import os
import json
import unicodedata
from typing import Dict, List, Tuple, Optional

# Standard key symbol aliases
KEY_ALIASES = {
    'semicolon': ';',
    'colon': ':',
    'comma': ',',
    'dot': '.',
    'period': '.',
    'slash': '/',
    'quote': "'",
    'space': ' ',
    'holder1': ' ',   # Left Thumb Shift (Muhenkan / Left Space)
    'holder2': '　',  # Right Thumb Shift (Henkan / Right Space / Full-width space)
    'shift': '',
    'minus': '-',
    'caret': '^',
    'backslash': '\\',
    'bracketleft': '[',
    'bracketright': ']',
    'at': '@'
}

def normalize_key_token(token: str) -> str:
    """Normalize key string to lowercase single char or alias."""
    token = token.strip()
    lower = token.lower()
    if lower in KEY_ALIASES:
        return KEY_ALIASES[lower]
    return lower

def katakana_to_hiragana(text: str) -> str:
    """Convert all Katakana characters into Hiragana."""
    result = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        elif ch == 'ヴ':
            result.append('ゔ')
        else:
            result.append(ch)
    return "".join(result)

class StrokeEvent:
    """Represents a single typing event: either a single keystroke or a simultaneous chord."""
    def __init__(self, keys: List[str], is_chord: bool = False, kana: str = ""):
        self.keys = [k.lower() for k in keys]
        self.is_chord = is_chord
        self.kana = kana

    def __repr__(self):
        if self.is_chord:
            return f"Chord({'+'.join(self.keys)})"
        return f"Key({'+'.join(self.keys)})"

class LayoutConverter:
    def __init__(self, keymap_path: str, romaji_table_path: str = "data/romaji_tables/standard_romaji.json"):
        with open(keymap_path, "r", encoding="utf-8") as f:
            self.keymap = json.load(f)
            
        with open(romaji_table_path, "r", encoding="utf-8") as f:
            self.romaji_table = json.load(f).get("table", {})
            
        self.name = self.keymap.get("name", os.path.basename(keymap_path))
        self.behavior_type = self.keymap.get("behavior", {}).get("type", "sequential")
        self.target_script = self.keymap.get("targetScript", "")
        self.shift_type = self.keymap.get("shiftType", "")
        
        # Check if the layout uses SandS (single space key shift)
        roles = self.keymap.get("roles", {})
        h1_keys = [str(k).lower() for k in roles.get("holder1", {}).get("keys", [])]
        self.is_sands = (self.shift_type.lower() == "sands") or (
            len(roles) == 1 and "holder1" in roles and "holder2" not in roles and "space" in h1_keys
        )
        
        # Build kana -> (flat_stroke, chord_annotated_stroke, is_chord, key_list) lookup
        self.kana_to_stroke: Dict[str, Tuple[str, str, bool, List[str]]] = {}
        self._build_lookup_table()

    def _build_lookup_table(self):
        behavior = self.keymap.get("behavior", {})
        config = behavior.get("config", {})
        
        # 1. Direct inputMappings (e.g. Tsuki 2-263: Sequential pre-shift)
        input_mappings = self.keymap.get("inputMappings", {})
        if input_mappings:
            for stroke, kana in input_mappings.items():
                if stroke.startswith("_comment"):
                    continue
                if kana:
                    kana = katakana_to_hiragana(kana)
                    norm_keys = [normalize_key_token(c) for c in stroke]
                    flat_stroke = "".join(norm_keys)
                    if kana not in self.kana_to_stroke or len(stroke) < len(self.kana_to_stroke[kana][0]):
                        self.kana_to_stroke[kana] = (flat_stroke, flat_stroke, False, norm_keys)
                        
        # 2. Chord lookupTable (e.g. Naginata, Shin-Geta, Nicola: Simultaneous chords)
        lookup_table = config.get("lookupTable", {}) or self.keymap.get("lookupTable", {})
        if lookup_table:
            for chord_str, kana in lookup_table.items():
                if chord_str.startswith("_comment") or not kana:
                    continue
                kana = katakana_to_hiragana(kana)
                keys = chord_str.split("+") if "+" in chord_str else chord_str.split()
                norm_keys = [normalize_key_token(k) for k in keys if normalize_key_token(k)]
                flat_stroke = "".join(norm_keys)
                is_chord = len(norm_keys) > 1
                chord_stroke = f"({'+'.join(norm_keys)})" if is_chord else flat_stroke
                
                if kana not in self.kana_to_stroke or len(flat_stroke) < len(self.kana_to_stroke[kana][0]):
                    self.kana_to_stroke[kana] = (flat_stroke, chord_stroke, is_chord, norm_keys)

        # 3. Positional / Logical Layout Mapping for Romaji (e.g. Onishi layout, Colemak Romaji)
        layout_mapping = self.keymap.get("keyRemap", {}) or self.keymap.get("layoutMapping", {})
        if layout_mapping:
            char_to_qwerty = {}
            for q_key, logical_char in layout_mapping.items():
                if q_key.startswith("_comment"):
                    continue
                char_to_qwerty[logical_char.lower()] = q_key.lower()
                
            for kana, romaji_str in self.romaji_table.items():
                kana = katakana_to_hiragana(kana)
                norm_keys = [char_to_qwerty.get(c.lower(), c.lower()) for c in romaji_str]
                qwerty_stroke = "".join(norm_keys)
                self.kana_to_stroke[kana] = (qwerty_stroke, qwerty_stroke, False, norm_keys)

        # 4. Fallback for pure Romaji / AZIK sequential
        if not self.kana_to_stroke:
            for kana, romaji_str in self.romaji_table.items():
                kana = katakana_to_hiragana(kana)
                norm_keys = [c.lower() for c in romaji_str]
                self.kana_to_stroke[kana] = (romaji_str, romaji_str, False, norm_keys)

    def _resolve_kana_stroke(self, pat: str, text: str, idx: int, sorted_patterns: List[str]) -> Tuple[str, str, bool, List[str]]:
        """Resolve keystrokes for kana, applying real-world IME optimizations (such as single 'n' before consonants)."""
        flat_str, ann_str, is_chord, keys = self.kana_to_stroke[pat]
        
        # Smart single 'n' optimization for Romaji-based layouts (matching real Japanese IME behavior)
        is_romaji = "a" in self.kana_to_stroke.get("あ", ("", "", False, []))[0]
        if is_romaji and pat == "ん" and len(keys) >= 2:
            rem = text[idx + len(pat):]
            next_keys = []
            if rem:
                for npat in sorted_patterns:
                    if rem.startswith(npat):
                        next_keys = self.kana_to_stroke[npat][3]
                        break
            
            next_first = next_keys[0].lower() if next_keys else ""
            # Consonants where single 'n' triggers 'ん' in standard IMEs
            single_n_consonants = set("ksthmrwgzjdbpfvc")
            # If at end of word/punctuation or followed by valid consonant: use single 'n'
            if not rem or rem[0] in "\n\r\t 、。！？!?,. " or next_first in single_n_consonants:
                single_k = keys[0]
                return single_k, single_k, False, [single_k]
                
        return flat_str, ann_str, is_chord, keys

    def convert_text(self, text: str) -> Tuple[str, str, int]:
        """Convert Japanese text into (flat_keystrokes, chord_annotated_keystrokes, chord_count)."""
        text = unicodedata.normalize('NFKC', text)
        text = katakana_to_hiragana(text)
        
        flat_result = []
        annotated_result = []
        chord_count = 0
        
        i = 0
        n = len(text)
        sorted_patterns = sorted(self.kana_to_stroke.keys(), key=len, reverse=True)
        
        while i < n:
            matched = False
            for pat in sorted_patterns:
                if text.startswith(pat, i):
                    flat_str, ann_str, is_chord, _ = self._resolve_kana_stroke(pat, text, i, sorted_patterns)
                    flat_result.append(flat_str)
                    annotated_result.append(ann_str)
                    if is_chord:
                        chord_count += 1
                    i += len(pat)
                    matched = True
                    break
            
            if not matched:
                char = text[i]
                if char in self.romaji_table:
                    stroke = self.romaji_table[char]
                    flat_result.append(stroke)
                    annotated_result.append(stroke)
                elif char in "\n\r\t ":
                    flat_result.append(char)
                    annotated_result.append(char)
                elif char in "ー-":
                    flat_result.append("-")
                    annotated_result.append("-")
                elif char in "、,":
                    flat_result.append(",")
                    annotated_result.append(",")
                elif char in "。.":
                    flat_result.append(".")
                    annotated_result.append(".")
                elif char in "！？!?":
                    flat_result.append("!")
                    annotated_result.append("!")
                i += 1
                
        return "".join(flat_result), "".join(annotated_result), chord_count

    def convert_to_events(self, text: str) -> List[StrokeEvent]:
        """Convert Japanese text into a structured list of StrokeEvents (handling chords vs sequential)."""
        text = unicodedata.normalize('NFKC', text)
        text = katakana_to_hiragana(text)
        
        events: List[StrokeEvent] = []
        i = 0
        n = len(text)
        sorted_patterns = sorted(self.kana_to_stroke.keys(), key=len, reverse=True)
        
        while i < n:
            matched = False
            for pat in sorted_patterns:
                if text.startswith(pat, i):
                    flat_str, ann_str, is_chord, keys = self._resolve_kana_stroke(pat, text, i, sorted_patterns)
                    if is_chord:
                        events.append(StrokeEvent(keys=keys, is_chord=True, kana=pat))
                    else:
                        for k in keys:
                            events.append(StrokeEvent(keys=[k], is_chord=False, kana=pat))
                    i += len(pat)
                    matched = True
                    break
            
            if not matched:
                char = text[i]
                if char in self.romaji_table:
                    stroke = self.romaji_table[char]
                    for k in stroke:
                        events.append(StrokeEvent(keys=[k], is_chord=False, kana=char))
                elif char in "\n\r\t ":
                    events.append(StrokeEvent(keys=[char], is_chord=False, kana=char))
                elif char in "ー-":
                    events.append(StrokeEvent(keys=["-"], is_chord=False, kana="ー"))
                elif char in "、,":
                    events.append(StrokeEvent(keys=[","], is_chord=False, kana="、"))
                elif char in "。.":
                    events.append(StrokeEvent(keys=["."], is_chord=False, kana="。"))
                elif char in "！？!?":
                    events.append(StrokeEvent(keys=["!"], is_chord=False, kana="!"))
                i += 1
                
        return events

def convert_corpus_for_all_keymaps(
    corpus_file: str = "data/corpus/source_hiragana.txt",
    keymaps_dir: str = "data/keymaps",
    output_dir: str = "data/generated",
    chords_output_dir: str = "data/chords_generated"
) -> Dict[str, Tuple[str, str, int]]:
    """Convert the corpus text for all keymap JSON files and save to both output directories."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(chords_output_dir, exist_ok=True)
    with open(corpus_file, "r", encoding="utf-8") as f:
        text = f.read()
        
    outputs = {}
    for filename in sorted(os.listdir(keymaps_dir)):
        if not filename.endswith(".json"):
            continue
        layout_id = filename[:-5]
        keymap_path = os.path.join(keymaps_dir, filename)
        
        romaji_table = "data/romaji_tables/azik.json" if "azik" in layout_id.lower() and os.path.exists("data/romaji_tables/azik.json") else "data/romaji_tables/standard_romaji.json"
        
        converter = LayoutConverter(keymap_path, romaji_table)
        flat_keystrokes, annotated_keystrokes, chord_count = converter.convert_text(text)
        
        # 1. Pure physical keystrokes
        out_filename = f"{layout_id}.source.txt"
        out_path = os.path.join(output_dir, out_filename)
        if not os.path.exists(out_path) or open(out_path, "r", encoding="utf-8").read() != flat_keystrokes:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(flat_keystrokes)
            
        # 2. Chord annotated keystrokes with (k1+k2) notation
        chord_out_path = os.path.join(chords_output_dir, out_filename)
        if not os.path.exists(chord_out_path) or open(chord_out_path, "r", encoding="utf-8").read() != annotated_keystrokes:
            with open(chord_out_path, "w", encoding="utf-8") as f:
                f.write(annotated_keystrokes)
            
        outputs[layout_id] = (out_path, chord_out_path, chord_count)
        
    return outputs
