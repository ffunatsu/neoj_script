"""
NeoJ-B: Biomechanical Typing Fluency, Awkwardness & Bottleneck Analyzer.
Quantifies:
1. Severe & Mild Scissors (ハサミ討ち・同手段交差)
2. Awkward vs Natural Simultaneous Chords (同手異段・離れコード vs 親指シフト・同段隣接)
3. Same-Finger Bigrams (SFB) and Disjoint Same-Finger (DSFB / Skipgrams)
4. Roll Direction & Zigzag Redirection (インロール vs アウトロール vs 運指反転)
5. One-Hand Overload Runs (同手連続打鍵スタッター)
6. Word-Level Comfort Distribution (Smooth % vs Awkward %, 95th Percentile Worst Bottleneck)
7. Hall of Fame for Worst-Case Words with Diagnostic Reasons
"""
import math
from typing import Dict, List, Tuple, Optional, Any
from .keyboard import (
    StandardKeyboard, KeyInfo, which_hand,
    LEFT_PINKY, LEFT_RING, LEFT_MIDDLE, LEFT_INDEX, LEFT_THUMB,
    RIGHT_THUMB, RIGHT_INDEX, RIGHT_MIDDLE, RIGHT_RING, RIGHT_PINKY
)
from .converter import StrokeEvent, LayoutConverter

# Biomechanical finger strain multipliers for micro-strain:
# Pinky (1.4), Ring (1.25), Middle (1.0), Index (1.0), Thumb (1.1)
FINGER_WEIGHTS = {
    LEFT_PINKY: 1.4, LEFT_RING: 1.25, LEFT_MIDDLE: 1.0, LEFT_INDEX: 1.0, LEFT_THUMB: 1.1,
    RIGHT_THUMB: 1.1, RIGHT_INDEX: 1.0, RIGHT_MIDDLE: 1.0, RIGHT_RING: 1.25, RIGHT_PINKY: 1.4
}

FINGER_NAMES_JA = {
    LEFT_PINKY: "左小", LEFT_RING: "左薬", LEFT_MIDDLE: "左中", LEFT_INDEX: "左人", LEFT_THUMB: "左親",
    RIGHT_THUMB: "右親", RIGHT_INDEX: "右人", RIGHT_MIDDLE: "右中", RIGHT_RING: "右薬", RIGHT_PINKY: "右小"
}

class WordAnalysisResult:
    """Detailed analysis for a single word."""
    def __init__(self, word: str, weight: int):
        self.word = word
        self.weight = weight
        self.keystrokes_repr = ""
        self.stroke_count = 0
        self.total_strain = 0.0
        self.peak_strain = 0.0
        self.difficulty_score = 0.0
        self.is_smooth = False
        self.is_awkward = False
        self.severe_scissors = 0
        self.mild_scissors = 0
        self.awkward_chords = 0
        self.sfbs = 0
        self.dsfbs = 0
        self.worst_transition_desc = ""
        self.pleasant_reason_desc = ""


class LayoutAnalysisResultB:
    """Comprehensive NeoJ-B evaluation result for a keyboard layout."""
    def __init__(self, layout_id: str, layout_name: str):
        self.layout_id = layout_id
        self.layout_name = layout_name
        self.total_words_evaluated = 0
        
        # Word Distribution Metrics
        self.smooth_words_ratio_pct = 0.0    # % of words with strain < 1.5
        self.moderate_words_ratio_pct = 0.0  # % of words with 1.5 <= strain < 3.5
        self.awkward_words_ratio_pct = 0.0   # % of words with strain >= 3.5 (bottlenecks)
        
        self.avg_word_difficulty = 0.0
        self.p95_worst_strain = 0.0
        self.p99_worst_strain = 0.0
        
        # Micro-Strain Rates (per 100 words)
        self.severe_scissors_rate = 0.0
        self.mild_scissors_rate = 0.0
        self.awkward_chords_rate = 0.0
        self.sfb_rate = 0.0
        self.dsfb_rate = 0.0
        self.zigzag_rate = 0.0
        
        # NeoJ-B Composite Fluency & Comfort Score (0 - 100)
        self.fluency_score = 0.0
        
        # Worst words hall of fame (Top 10 hardest words)
        self.worst_words: List[WordAnalysisResult] = []
        # Best words hall of fame (Top 10 most comfortable flowing words)
        self.best_words: List[WordAnalysisResult] = []


class FluencyAnalyzerB:
    """Engine to analyze typing fluency, awkwardness, and word bottlenecks."""
    def __init__(self):
        self.kb = StandardKeyboard()

    def evaluate_chord_strain(self, event: StrokeEvent) -> Tuple[float, str, bool]:
        """
        Evaluate biomechanical awkwardness of a simultaneous chord.
        Returns: (strain_score, diagnostic_desc, is_awkward)
        """
        if not event.is_chord or len(event.keys) < 2:
            return 0.0, "", False

        k_infos = [self.kb.get_key(k) for k in event.keys]
        k_infos = [k for k in k_infos if k is not None]
        if len(k_infos) < 2:
            return 0.2, "Standard Chord", False

        # Check if thumb shift (NICOLA style or SandS space chord)
        has_thumb = any(k.finger in (LEFT_THUMB, RIGHT_THUMB) for k in k_infos)
        if has_thumb:
            thumb_key = next(k for k in k_infos if k.finger in (LEFT_THUMB, RIGHT_THUMB))
            non_thumbs = [k for k in k_infos if k.finger not in (LEFT_THUMB, RIGHT_THUMB)]
            if len(non_thumbs) == 1:
                char_key = non_thumbs[0]
                t_hand = which_hand(thumb_key.finger)
                c_hand = which_hand(char_key.finger)
                hand_name = "左手" if c_hand == "left" else "右手"
                if t_hand != c_hand:
                    return 0.40, "両手親指シフト (Bilateral)", False
                else:
                    # Same-hand thumb chord (pinch stretch)
                    span = abs(char_key.finger - thumb_key.finger)
                    fc_name = FINGER_NAMES_JA.get(char_key.finger, str(char_key.finger))
                    if span <= 1:
                        return 0.45, f"{hand_name}親指人差同時({char_key.char})", False
                    elif span == 2:
                        return 0.70, f"{hand_name}親指中指同時({char_key.char})", False
                    elif span == 3:
                        return 1.20, f"{hand_name}親指薬指ピンチ同時({char_key.char})", False
                    else:
                        return 2.00, f"{hand_name}親指小指ストレッチ同時({char_key.char})", True
            return 0.8, "親指複合同時", False

        # Check if cross-hand chord (e.g. Shin-Geta cross hand, Naginata cross hand)
        hands = {which_hand(k.finger) for k in k_infos}
        if "left" in hands and "right" in hands and len(k_infos) == 2:
            return 0.35, "両手同時打鍵", False

        # Same-hand simultaneous chord
        k1, k2 = k_infos[0], k_infos[1]
        hand_name = "左手" if which_hand(k1.finger) == "left" else "右手"
        row_diff = abs(k1.row - k2.row)
        col_diff = abs(k1.col - k2.col)
        f_diff = abs(k1.finger - k2.finger)
        
        f1_name = FINGER_NAMES_JA.get(k1.finger, str(k1.finger))
        f2_name = FINGER_NAMES_JA.get(k2.finger, str(k2.finger))

        # (A) Same-hand cross-row chord (Severe strain!)
        if row_diff >= 2:
            desc = f"{hand_name}異段同時({f1_name}+{f2_name} 段差2: {k1.char}+{k2.char})"
            return 4.5, desc, True
        elif row_diff == 1:
            if f_diff == 0:
                return 5.0, f"{hand_name}同指異段({f1_name}: {k1.char}+{k2.char})", True
            elif col_diff >= 2:
                desc = f"{hand_name}斜め離れ同時({f1_name}+{f2_name}: {k1.char}+{k2.char})"
                return 3.5, desc, True
            else:
                desc = f"{hand_name}異段隣接同時({f1_name}+{f2_name}: {k1.char}+{k2.char})"
                return 2.0, desc, False

        # (B) Same-hand same-row chord
        if row_diff == 0:
            if col_diff == 1 and f_diff == 1:
                return 0.4, f"{hand_name}同段隣接同時({f1_name}+{f2_name}: {k1.char}+{k2.char})", False
            elif col_diff >= 2:
                desc = f"{hand_name}同段離れ同時({f1_name}+{f2_name}: {k1.char}+{k2.char})"
                return 2.8, desc, True

        return 1.0, f"{hand_name}同時({k1.char}+{k2.char})", False

    def evaluate_transition_strain(
        self, prev_event: StrokeEvent, cur_event: StrokeEvent, next_event: Optional[StrokeEvent] = None
    ) -> Tuple[float, str, bool, bool, bool, bool]:
        """
        Evaluate biomechanical strain between consecutive events.
        Returns: (strain, desc, is_severe_scissor, is_mild_scissor, is_sfb, is_dsfb)
        """
        # 1. Check for Thumb repetition (Moderate cadence strain)
        prev_thumbs = [self.kb.get_key(k).finger for k in prev_event.keys if self.kb.get_key(k) and self.kb.get_key(k).finger in (LEFT_THUMB, RIGHT_THUMB)]
        cur_thumbs = [self.kb.get_key(k).finger for k in cur_event.keys if self.kb.get_key(k) and self.kb.get_key(k).finger in (LEFT_THUMB, RIGHT_THUMB)]
        thumb_strain = 0.0
        thumb_desc = ""
        if prev_thumbs and cur_thumbs and prev_thumbs[0] == cur_thumbs[0]:
            thumb_name = "左親" if prev_thumbs[0] == LEFT_THUMB else "右親"
            thumb_strain = 0.35
            thumb_desc = f"[{thumb_name}連続]"

        # 2. Extract character keys for inter-character motion analysis
        p_char_keys = [k for k in prev_event.keys if self.kb.get_key(k) and self.kb.get_key(k).finger not in (LEFT_THUMB, RIGHT_THUMB)]
        c_char_keys = [k for k in cur_event.keys if self.kb.get_key(k) and self.kb.get_key(k).finger not in (LEFT_THUMB, RIGHT_THUMB)]
        p_key = p_char_keys[0] if p_char_keys else (prev_event.keys[0] if prev_event.keys else "")
        c_key = c_char_keys[0] if c_char_keys else (cur_event.keys[0] if cur_event.keys else "")
        
        kp = self.kb.get_key(p_key)
        kc = self.kb.get_key(c_key)
        if not kp or not kc:
            return thumb_strain, thumb_desc, False, False, False, False

        fp, fc = kp.finger, kc.finger
        hp, hc = which_hand(fp), which_hand(fc)
        wp, wc = FINGER_WEIGHTS.get(fp, 1.0), FINGER_WEIGHTS.get(fc, 1.0)
        avg_w = (wp + wc) / 2.0

        if hp != hc or hp == "none":
            desc = f"交互打鍵 (Smooth) {thumb_desc}".strip()
            return 0.1 + thumb_strain, desc, False, False, False, False

        hand_ja = "左手" if hp == "left" else "右手"
        fp_name = FINGER_NAMES_JA.get(fp, str(fp))
        fc_name = FINGER_NAMES_JA.get(fc, str(fc))

        # 1. SFB (Same Finger Bigram)
        if fp == fc:
            if fp not in (LEFT_THUMB, RIGHT_THUMB):
                row_jump = abs(kp.row - kc.row)
                if row_jump >= 2:
                    desc = f"{hand_ja}{fp_name}同指段飛び({kp.char}→{kc.char}) {thumb_desc}".strip()
                    return 3.8 * avg_w + thumb_strain, desc, False, False, True, False
                else:
                    desc = f"{hand_ja}{fp_name}同指連打({kp.char}→{kc.char}) {thumb_desc}".strip()
                    return 2.2 * avg_w + thumb_strain, desc, False, False, True, False

        # 2. Scissors (ハサミ討ち / 同手異指の段交差運動)
        if fp not in (LEFT_THUMB, RIGHT_THUMB) and fc not in (LEFT_THUMB, RIGHT_THUMB):
            row_diff = abs(kp.row - kc.row)
            f_diff = abs(fp - fc)
            
            # Severe Scissor: ONLY adjacent fingers (f_diff == 1: e.g. 中指↔薬指, 薬指↔小指) with 2+ row difference (shear strain on shared tendons)
            if row_diff >= 2 and f_diff == 1:
                desc = f"{hand_ja}重度シザーズ({fp_name}[R{kp.row}]→{fc_name}[R{kc.row}]: {kp.char}→{kc.char}) {thumb_desc}".strip()
                return 3.5 * avg_w + thumb_strain, desc, True, False, False, False
                
            # Non-adjacent fingers spanning 2+ rows (f_diff >= 2: e.g. 人差し指↔薬指 M->O): Mild Diagonal Stretch, not Severe Scissor
            if row_diff >= 2 and f_diff >= 2:
                desc = f"{hand_ja}斜め伸展({fp_name}→{fc_name}: {kp.char}→{kc.char}) {thumb_desc}".strip()
                return 1.2 * avg_w + thumb_strain, desc, False, True, False, False

            # Mild Scissor: 1 row difference with antagonistic finger movement
            if row_diff == 1 and f_diff == 1:
                is_cross = (kp.row < kc.row and fp > fc) or (kp.row > kc.row and fp < fc)
                if is_cross:
                    desc = f"{hand_ja}軽度シザーズ({fp_name}→{fc_name}: {kp.char}→{kc.char}) {thumb_desc}".strip()
                    return 1.4 * avg_w + thumb_strain, desc, False, True, False, False


        # 3. DSFB (Disjoint SFB / Skipgram)
        is_dsfb = False
        if next_event and next_event.keys:
            n_char_keys = [k for k in next_event.keys if self.kb.get_key(k) and self.kb.get_key(k).finger not in (LEFT_THUMB, RIGHT_THUMB)]
            n_key = n_char_keys[0] if n_char_keys else (next_event.keys[0] if next_event.keys else "")
            kn = self.kb.get_key(n_key)
            if kn and kn.finger == fp and fp not in (LEFT_THUMB, RIGHT_THUMB):
                is_dsfb = True
                desc = f"{hand_ja}{fp_name}挟み同指({kp.char}→{kc.char}→{kn.char}) {thumb_desc}".strip()
                return 1.2 * avg_w + thumb_strain, desc, False, False, False, True

        # 4. Roll Direction
        if fp not in (LEFT_THUMB, RIGHT_THUMB) and fc not in (LEFT_THUMB, RIGHT_THUMB):
            is_in_roll = (hp == "left" and fp < fc) or (hp == "right" and fp > fc)
            if is_in_roll:
                desc = f"インロール (Smooth) {thumb_desc}".strip()
                return 0.2 * avg_w + thumb_strain, desc, False, False, False, False
            else:
                desc = f"アウトロール {thumb_desc}".strip()
                return 0.5 * avg_w + thumb_strain, desc, False, False, False, False

        desc = f"同手打鍵 {thumb_desc}".strip()
        return 0.3 * avg_w + thumb_strain, desc, False, False, False, False


    def analyze_word(self, converter: LayoutConverter, word: str, weight: int = 50) -> WordAnalysisResult:
        """Analyze keystroke fluency and awkwardness for a specific Japanese word."""
        res = WordAnalysisResult(word=word, weight=weight)
        events = converter.convert_to_events(word)
        res.stroke_count = len(events)
        if res.stroke_count == 0:
            return res

        worst_strain = 0.0
        worst_desc = ""

        # 1. Analyze individual chords
        for ev in events:
            if ev.is_chord:
                c_strain, c_desc, is_awk = self.evaluate_chord_strain(ev)
                res.total_strain += c_strain
                if is_awk:
                    res.awkward_chords += 1
                if c_strain > worst_strain:
                    worst_strain = c_strain
                    worst_desc = c_desc

        # 2. Analyze transitions
        for i in range(len(events) - 1):
            prev_ev = events[i]
            cur_ev = events[i + 1]
            next_ev = events[i + 2] if i + 2 < len(events) else None
            
            t_strain, t_desc, is_sev_sc, is_mild_sc, is_sfb, is_dsfb = self.evaluate_transition_strain(
                prev_ev, cur_ev, next_ev
            )
            res.total_strain += t_strain
            if is_sev_sc:
                res.severe_scissors += 1
            if is_mild_sc:
                res.mild_scissors += 1
            if is_sfb:
                res.sfbs += 1
            if is_dsfb:
                res.dsfbs += 1
                
            if t_strain > worst_strain:
                worst_strain = t_strain
                worst_desc = t_desc

        res.peak_strain = worst_strain
        res.worst_transition_desc = worst_desc
        
        # Build human-readable QWERTY keystroke representation
        repr_chunks = []
        is_sands = getattr(converter, "is_sands", False)
        def clean_key_name(k: str) -> str:
            kl = k.lower()
            if kl in ('quotekey', 'quote', "'"): return "'"
            if kl in ('semicolon', ';'): return ';'
            if kl in ('slash', '/'): return '/'
            if kl in ('comma', ','): return ','
            if kl in ('period', '.'): return '.'
            if kl in ('hyphen', 'minus', '-'): return '-'
            return k

        for ev in events:
            if ev.is_chord:
                k_strs = []
                for k in ev.keys:
                    if k in (' ', '　'):
                        k_strs.append('Sp' if is_sands else ('左親' if k == ' ' else '右親'))
                    else:
                        k_strs.append(clean_key_name(k))
                repr_chunks.append(f"({'+'.join(k_strs)})")
            else:
                k = ev.keys[0] if ev.keys else ""
                if k in (' ', '　'):
                    repr_chunks.append('Sp' if is_sands else ('左親' if k == ' ' else '右親'))
                else:
                    repr_chunks.append(clean_key_name(k))
        res.keystrokes_repr = " ".join(repr_chunks)


        
        avg_strain = res.total_strain / max(1, res.stroke_count)
        res.difficulty_score = avg_strain + (res.peak_strain * 0.5)

        if res.difficulty_score < 1.5 and res.severe_scissors == 0 and res.awkward_chords == 0 and res.sfbs == 0:
            res.is_smooth = True
        elif res.difficulty_score >= 3.2 or res.severe_scissors >= 1 or res.awkward_chords >= 1:
            res.is_awkward = True

        # Determine pleasant flow reason if smooth
        if res.is_smooth:
            hands = []
            rows = []
            for ev in events:
                if ev.keys:
                    k = ev.keys[0]
                    kinfo = self.kb.get_key(k)
                    if kinfo:
                        hands.append(which_hand(kinfo.finger))
                        rows.append(kinfo.row)

            hand_changes = sum(1 for i in range(len(hands) - 1) if hands[i] != hands[i + 1] and hands[i] in ("left", "right") and hands[i + 1] in ("left", "right"))
            total_trans = max(1, len(hands) - 1)
            alt_rate = hand_changes / total_trans

            home_pct = sum(1 for r in rows if r == 2) / max(1, len(rows))

            reasons = []
            if alt_rate >= 0.95 and len(events) >= 3:
                reasons.append("完全左右交互打鍵")
            elif alt_rate >= 0.70 and len(events) >= 3:
                reasons.append(f"高交互打鍵({int(alt_rate*100)}%)")

            if home_pct >= 0.75:
                reasons.append("ホーム段集約")
            elif home_pct >= 0.50:
                reasons.append("ホームポジション中心")

            inward_rolls = 0
            for i in range(len(events) - 1):
                if not events[i].is_chord and not events[i + 1].is_chord:
                    k1 = events[i].keys[0]
                    k2 = events[i + 1].keys[0]
                    ki1 = self.kb.get_key(k1)
                    ki2 = self.kb.get_key(k2)
                    if ki1 and ki2 and which_hand(ki1.finger) == which_hand(ki2.finger) and which_hand(ki1.finger) in ("left", "right"):
                        f1, f2 = ki1.finger, ki2.finger
                        if which_hand(f1) == "left" and f1 < f2:
                            inward_rolls += 1
                        elif which_hand(f1) == "right" and f1 > f2:
                            inward_rolls += 1

            if inward_rolls >= 1:
                reasons.append("内向きスムーズロール")

            if not reasons:
                reasons.append("段交差なし・軽快リズム運指")

            res.pleasant_reason_desc = "・".join(reasons[:2])

        return res


    def analyze_layout_corpus(
        self, layout_id: str, layout_name: str, converter: LayoutConverter, word_corpus: List[Tuple[str, int]]
    ) -> LayoutAnalysisResultB:
        """Run large-scale vocabulary evaluation across the word corpus for a given layout."""
        result = LayoutAnalysisResultB(layout_id=layout_id, layout_name=layout_name)
        result.total_words_evaluated = len(word_corpus)

        total_weight = 0
        weighted_smooth = 0.0
        weighted_awkward = 0.0
        weighted_difficulty = 0.0
        
        total_sev_scissors = 0
        total_mild_scissors = 0
        total_awk_chords = 0
        total_sfbs = 0
        total_dsfbs = 0

        word_results: List[WordAnalysisResult] = []

        for word, weight in word_corpus:
            w_res = self.analyze_word(converter, word, weight)
            word_results.append(w_res)
            
            total_weight += weight
            if w_res.is_smooth:
                weighted_smooth += weight
            elif w_res.is_awkward:
                weighted_awkward += weight
                
            weighted_difficulty += w_res.difficulty_score * weight
            total_sev_scissors += w_res.severe_scissors * weight
            total_mild_scissors += w_res.mild_scissors * weight
            total_awk_chords += w_res.awkward_chords * weight
            total_sfbs += w_res.sfbs * weight
            total_dsfbs += w_res.dsfbs * weight

        # Ratios
        result.smooth_words_ratio_pct = (weighted_smooth / max(1, total_weight)) * 100.0
        result.awkward_words_ratio_pct = (weighted_awkward / max(1, total_weight)) * 100.0
        result.moderate_words_ratio_pct = max(0.0, 100.0 - result.smooth_words_ratio_pct - result.awkward_words_ratio_pct)
        result.avg_word_difficulty = weighted_difficulty / max(1, total_weight)

        # Micro-strain rates per 100 words
        base_factor = 100.0 / max(1, total_weight)
        result.severe_scissors_rate = total_sev_scissors * base_factor
        result.mild_scissors_rate = total_mild_scissors * base_factor
        result.awkward_chords_rate = total_awk_chords * base_factor
        result.sfb_rate = total_sfbs * base_factor
        result.dsfb_rate = total_dsfbs * base_factor

        # Calculate Percentiles (P95, P99) of peak strain
        sorted_by_peak = sorted(word_results, key=lambda x: x.peak_strain)
        p95_idx = int(len(sorted_by_peak) * 0.95)
        p99_idx = int(len(sorted_by_peak) * 0.99)
        result.p95_worst_strain = sorted_by_peak[p95_idx].peak_strain if sorted_by_peak else 0.0
        result.p99_worst_strain = sorted_by_peak[p99_idx].peak_strain if sorted_by_peak else 0.0

        # NeoJ-B Fluency & Comfort Score (0-100)
        fluency = (0.5 * result.smooth_words_ratio_pct) + (0.5 * (100.0 - result.awkward_words_ratio_pct))
        result.fluency_score = max(0.0, min(100.0, fluency))

        # Worst Words Hall of Fame (Top 10 sorted by difficulty_score descending)
        worst_sorted = sorted(word_results, key=lambda x: -x.difficulty_score)
        result.worst_words = worst_sorted[:10]

        # Best Words Hall of Fame (Top 10 sorted by difficulty_score ascending, prioritizing 3+ mora words)
        candidate_best = [w for w in word_results if len(w.word) >= 3 and w.is_smooth]
        if len(candidate_best) < 10:
            candidate_best = [w for w in word_results if w.is_smooth]
        best_sorted = sorted(candidate_best, key=lambda x: (x.difficulty_score, x.peak_strain, -x.weight, -len(x.word)))
        result.best_words = best_sorted[:10]

        return result

