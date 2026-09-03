"""
Physical Keyboard Geometry and Finger Mapping.
Accurately models Left Thumb Shift (' '), Right Thumb Shift ('　' full-width space), and Standard Keys.
"""
import math
from typing import Dict, List, Tuple, Optional

# Finger Constants
NONE = -1
LEFT_PINKY = 1
LEFT_RING = 2
LEFT_MIDDLE = 3
LEFT_INDEX = 4
LEFT_THUMB = 5
RIGHT_THUMB = 6
RIGHT_INDEX = 7
RIGHT_MIDDLE = 8
RIGHT_RING = 9
RIGHT_PINKY = 10

FINGER_NAMES = {
    LEFT_PINKY: "Left Pinky",
    LEFT_RING: "Left Ring",
    LEFT_MIDDLE: "Left Middle",
    LEFT_INDEX: "Left Index",
    LEFT_THUMB: "Left Thumb",
    RIGHT_THUMB: "Right Thumb",
    RIGHT_INDEX: "Right Index",
    RIGHT_MIDDLE: "Right Middle",
    RIGHT_RING: "Right Ring",
    RIGHT_PINKY: "Right Pinky"
}

def which_hand(finger_id: int) -> str:
    if 1 <= finger_id <= 5:
        return "left"
    elif 6 <= finger_id <= 10:
        return "right"
    return "none"

class KeyInfo:
    def __init__(self, key_id: int, char: str, row: int, col: int, x: float, y: float, w: float, h: float, finger: int):
        self.key_id = key_id
        self.char = char
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cx = x + w / 2.0
        self.cy = y + h / 2.0
        self.finger = finger

class StandardKeyboard:
    """Standard Physical Keyboard Model with distinct Left/Right Thumb keys."""
    def __init__(self):
        self.pixels_per_cm = 26.315789
        self.norm_key_size = 50.0
        self.keys: Dict[str, KeyInfo] = {}
        self.key_list: List[KeyInfo] = []
        self._build_keyboard()

    def _build_keyboard(self):
        # Row layout:
        # Row 1 has standard [ and ] keys
        # Row 4 has LCtrl, LAlt, ' ' (Left Space / Left Thumb), '　' (Right Space / Right Thumb), RAlt, RCtrl
        row_chars = [
            ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
            ['Tab', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
            ['Caps', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'Enter'],
            ['LShift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'RShift'],
            ['LCtrl', 'LMeta', 'LAlt', ' ', '　', 'RAlt', 'RCtrl']
        ]

        finger_grid = [
            [1, 1, 1, 2, 3, 4, 4, 7, 7, 8, 9, 10, 10, 10], # Row 0
            [1, 1, 2, 3, 4, 4, 7, 7, 8, 9, 10, 10, 10, 10], # Row 1: [ and ] are Right Pinky (10)
            [1, 1, 2, 3, 4, 4, 7, 7, 8, 9, 10, 10, 10],     # Row 2
            [1, 1, 2, 3, 4, 4, 7, 7, 8, 9, 10, 10],         # Row 3
            [1, 1, 1, 5, 6, 10, 10]                         # Row 4: ' ' is Left Thumb (5), '　' is Right Thumb (6)
        ]

        # Key widths
        key_widths = {
            (0, 13): 102.0,
            (1, 0): 76.0, (1, 13): 76.0,
            (2, 0): 89.0, (2, 12): 113.0,
            (3, 0): 116.0, (3, 11): 136.0,
            (4, 0): 60.0, (4, 1): 60.0, (4, 2): 60.0, (4, 3): 120.0, (4, 4): 120.0, (4, 5): 60.0, (4, 6): 60.0
        }

        key_id = 0
        cur_y = 0.5
        for row, chars in enumerate(row_chars):
            cur_x = 0.5
            for col, ch in enumerate(chars):
                w = key_widths.get((row, col), self.norm_key_size)
                h = self.norm_key_size
                finger = finger_grid[row][col] if col < len(finger_grid[row]) else 10
                kinfo = KeyInfo(key_id, ch, row, col, cur_x, cur_y, w, h, finger)
                self.keys[ch.lower()] = kinfo
                self.key_list.append(kinfo)
                cur_x += w + 2.0
                key_id += 1
            cur_y += self.norm_key_size + 2.0

        space_y = self.keys[' '].cy
        
        # Home resting positions (A S D F / J K L ;)
        # Left Thumb rests at Left Space (cx=215), Right Thumb rests at Right Space (cx=335)
        self.home_positions: Dict[int, Tuple[float, float]] = {
            LEFT_PINKY: (self.keys['a'].cx, self.keys['a'].cy),
            LEFT_RING: (self.keys['s'].cx, self.keys['s'].cy),
            LEFT_MIDDLE: (self.keys['d'].cx, self.keys['d'].cy),
            LEFT_INDEX: (self.keys['f'].cx, self.keys['f'].cy),
            LEFT_THUMB: (self.keys[' '].cx, space_y),
            RIGHT_THUMB: (self.keys['　'].cx, space_y),
            RIGHT_INDEX: (self.keys['j'].cx, self.keys['j'].cy),
            RIGHT_MIDDLE: (self.keys['k'].cx, self.keys['k'].cy),
            RIGHT_RING: (self.keys['l'].cx, self.keys['l'].cy),
            RIGHT_PINKY: (self.keys[';'].cx, self.keys[';'].cy)
        }

    def get_key(self, char: str) -> Optional[KeyInfo]:
        ch = char.lower()
        if ch in self.keys:
            return self.keys[ch]
        if ch == ' ':
            return self.keys[' ']
        if ch == '　':
            return self.keys['　']
        if ch in ('\n', '\r'):
            return self.keys.get('enter')
        return None
