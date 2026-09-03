"""
Biomechanical Keyboard Typing Workload Analyzer.
Accurately models:
1. Mechanical switch actuation work (Dominant ~75-80%)
2. Planar travel movement across keytops (~10%)
3. Row Reach Strain (Number row wrist elevation vs Home row comfort) (~7-10%)
4. Lateral Pinky Stretch Strain (Outermost columns: [, ], ', =, -, \\) (~3-5%)
5. Same-Finger-Bigram (SFB) muscle fatigue penalty (~3%)
6. Sync-aware chord synchronization cost (Reference mode)
"""
import math
from typing import Dict, List, Tuple, Optional
from .keyboard import (
    StandardKeyboard, KeyInfo, which_hand,
    LEFT_PINKY, LEFT_RING, LEFT_MIDDLE, LEFT_INDEX, LEFT_THUMB,
    RIGHT_THUMB, RIGHT_INDEX, RIGHT_MIDDLE, RIGHT_RING, RIGHT_PINKY
)

class LayoutAnalysisResult:
    def __init__(self, layout_name: str, chord_count: int = 0):
        self.layout_name = layout_name
        self.chord_count = chord_count
        self.num_keys = 0
        self.total_distance_cm = 0.0
        
        # Energy Component Workloads (Arbitrary Effort Units: 1 unit ~ 1 actuation stroke)
        self.actuation_effort = 0.0     # Switch depression physical work
        self.travel_effort = 0.0        # Horizontal finger glide
        self.reach_effort = 0.0         # Row Reach + Lateral Pinky Stretch Strain
        self.sfb_effort = 0.0           # Consecutive same-finger fatigue
        
        self.pure_total_effort = 0.0    # Actuation + Travel + Reach + SFB
        self.pure_effort_per_char = 0.0
        
        self.sync_total_effort = 0.0    # Pure + Chords * 0.3
        self.sync_effort_per_char = 0.0
        
        # Biomechanical Distributions
        self.finger_usage: Dict[int, int] = {i: 0 for i in range(1, 11)}
        self.row_usage: Dict[int, int] = {i: 0 for i in range(5)}
        self.distance_per_finger: Dict[int, float] = {i: 0.0 for i in range(1, 11)}
        self.consec_finger_press: Dict[int, int] = {i: 0 for i in range(1, 11)}
        self.consec_hand_press: Dict[str, int] = {"left": 0, "right": 0}
        
        # Ergonomic Quality Ratios
        self.sfb_count = 0
        self.sfb_rate_pct = 0.0
        self.hand_alternation_rate_pct = 0.0
        self.kla_quality_score = 0.0

class KeyboardAnalyzer:
    def __init__(self):
        self.kb = StandardKeyboard()

    def analyze_keystrokes(
        self, layout_name: str, keystrokes: str, chord_count: int = 0, base_char_count: int = 1097
    ) -> LayoutAnalysisResult:
        """Run physical typing energy simulation based on mechanical switch actuation & row/lateral strain."""
        result = LayoutAnalysisResult(layout_name=layout_name, chord_count=chord_count)
        
        finger_positions: Dict[int, Tuple[float, float]] = self.kb.home_positions.copy()
        
        prev_finger: Optional[int] = None
        prev_char: Optional[str] = None
        prev_hand: Optional[str] = None
        
        # Biomechanical finger strain multipliers:
        # Middle (1.0), Index (1.0), Ring (1.15), Thumb (1.2), Pinky (1.3)
        finger_strain_weights = {
            LEFT_PINKY: 1.3, LEFT_RING: 1.15, LEFT_MIDDLE: 1.0, LEFT_INDEX: 1.0, LEFT_THUMB: 1.2,
            RIGHT_THUMB: 1.2, RIGHT_INDEX: 1.0, RIGHT_MIDDLE: 1.0, RIGHT_RING: 1.15, RIGHT_PINKY: 1.3
        }
        
        # Row reach penalties (Biomechanical wrist elevation and reaching strain)
        row_reach_penalties = {
            0: 1.5,   # Number row (Top): Wrist elevation, forearm extension
            1: 0.2,   # Upper row: Mild finger extension
            2: 0.0,   # Home row: Zero elevation / optimal rest
            3: 0.25,  # Lower row: Mild finger flexion
            4: 0.0    # Space row: Natural thumb rest
        }
        
        actuation_effort = 0.0
        travel_effort = 0.0
        reach_effort = 0.0
        sfb_effort = 0.0
        
        for char in keystrokes:
            if char in "\r\n\t":
                continue
                
            kinfo = self.kb.get_key(char)
            if not kinfo:
                continue
                
            result.num_keys += 1
            finger = kinfo.finger
            hand = which_hand(finger)
            strain_weight = finger_strain_weights.get(finger, 1.0)
            
            # --- 1. Mechanical Switch Actuation Work (Dominant: 1 stroke = 1.0 * finger strain) ---
            actuation_effort += 1.0 * strain_weight
            
            # --- 2. Planar Travel Work (~0.1 per cm) ---
            cur_pos = finger_positions[finger]
            target_pos = (kinfo.cx, kinfo.cy)
            dx = cur_pos[0] - target_pos[0]
            dy = cur_pos[1] - target_pos[1]
            dist_pixels = math.sqrt(dx * dx + dy * dy)
            dist_cm = dist_pixels / self.kb.pixels_per_cm
            
            result.distance_per_finger[finger] += dist_cm
            result.total_distance_cm += dist_cm
            finger_positions[finger] = target_pos
            
            travel_effort += (dist_cm * 0.1) * strain_weight
            
            # --- 3. Row Reach & Lateral Pinky Stretch Strain ---
            # (A) Vertical row elevation penalty
            row_penalty = row_reach_penalties.get(kinfo.row, 0.0)
            
            # (B) Lateral Pinky Stretch penalty (Outer columns beyond home column)
            lateral_penalty = 0.0
            if finger == RIGHT_PINKY:
                # Right Pinky home is col 10 (';', 'p', '/')
                if kinfo.col == 11:    # '[', "'", '-'
                    lateral_penalty = 0.6
                elif kinfo.col == 12:  # ']', '='
                    lateral_penalty = 1.2
                elif kinfo.col >= 13:  # '\\'
                    lateral_penalty = 1.8
            elif finger == LEFT_PINKY:
                # Left Pinky home is col 1 ('a', 'q', 'z')
                if kinfo.col == 0:     # '`', Tab, Caps
                    lateral_penalty = 0.6
                    
            reach_effort += (row_penalty + lateral_penalty) * strain_weight
            
            # --- 4. SFB Strain Penalty (Same finger rapid re-actuation) ---
            if prev_finger == finger and prev_char != char:
                result.consec_finger_press[finger] += 1
                sfb_effort += 0.5 * strain_weight
                
            if prev_hand is not None and prev_hand == hand and hand in ("left", "right"):
                result.consec_hand_press[hand] += 1
                
            result.finger_usage[finger] += 1
            result.row_usage[kinfo.row] += 1
            
            prev_finger = finger
            prev_char = char
            prev_hand = hand
            
        result.actuation_effort = actuation_effort
        result.travel_effort = travel_effort
        result.reach_effort = reach_effort
        result.sfb_effort = sfb_effort
        result.pure_total_effort = actuation_effort + travel_effort + reach_effort + sfb_effort
        result.pure_effort_per_char = result.pure_total_effort / max(1, base_char_count)
        
        # Sync-Aware Workload (Gentle synchronization cost: 0.3 effort per chord)
        chord_sync_cost = chord_count * 0.3
        result.sync_total_effort = result.pure_total_effort + chord_sync_cost
        result.sync_effort_per_char = result.sync_total_effort / max(1, base_char_count)
        
        self._score_result(result, base_char_count)
        return result

    def _score_result(self, r: LayoutAnalysisResult, base_char_count: int):
        """Calculate KLA reference quality metrics."""
        if r.num_keys == 0:
            return

        avg_dist = r.total_distance_cm / r.num_keys
        kla_dist = max(0.0, 4.0 - avg_dist) / 4.0
        
        f_scoring = {
            LEFT_PINKY: 0.8, LEFT_RING: 1.2, LEFT_MIDDLE: 3.5, LEFT_INDEX: 2.5, LEFT_THUMB: 1.0,
            RIGHT_THUMB: 1.0, RIGHT_INDEX: 2.5, RIGHT_MIDDLE: 3.5, RIGHT_RING: 1.2, RIGHT_PINKY: 0.8
        }
        total_f = 0.0
        for f_id, weight in f_scoring.items():
            pct = (r.finger_usage[f_id] / r.num_keys) * 100.0
            capped_pct = min(pct, 20.0)
            total_f += (capped_pct / 20.0) * weight
            
        finger_score = (total_f / 20.0) * 100.0
        
        total_sfb = sum(r.consec_finger_press.values())
        r.sfb_count = total_sfb
        r.sfb_rate_pct = (total_sfb / max(1, r.num_keys - 1)) * 100.0
        sfb_score = max(0.0, 100.0 - (r.sfb_rate_pct * 8.0))
        
        total_consec_hand = sum(r.consec_hand_press.values())
        r.hand_alternation_rate_pct = max(0.0, 100.0 - (total_consec_hand / max(1, r.num_keys - 1)) * 100.0)
        hand_score = r.hand_alternation_rate_pct
        
        r.kla_quality_score = (finger_score * 0.4) + (sfb_score * 0.3) + (hand_score * 0.3)
