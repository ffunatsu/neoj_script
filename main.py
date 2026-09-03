"""
neo-j: Japanese Keyboard Layout Benchmark Framework.
Evaluates keymap JSON definitions placed in data/keymaps/ and outputs physical & fluency metrics.
"""
import sys
import os
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.neo_j.corpus import setup_corpus, get_hiragana_text, get_word_corpus
from src.neo_j.converter import LayoutConverter, convert_corpus_for_all_keymaps
from src.neo_j.analyzer import KeyboardAnalyzer
from src.neo_j.analyzer_b import FluencyAnalyzerB
from src.neo_j.composite import CompositeAnalyzer
from src.neo_j.report import BenchmarkReporter

def run_benchmark(
    keymaps_dir: str = "data/keymaps",
    generated_dir: str = "data/generated",
    chords_dir: str = "data/chords_generated",
    mode: str = "all"
):
    keymap_files = [f for f in sorted(os.listdir(keymaps_dir)) if f.endswith(".json")]
    if not keymap_files:
        print(f"Info: {keymaps_dir} にキーマップ定義ファイル (.json) が存在しません。")
        print("キーマップJSONファイルを配置して再度実行してください。")
        return

    # 1. Corpus setup
    setup_corpus()
    hiragana_text = get_hiragana_text()
    word_corpus = get_word_corpus()
    base_char_count = len(hiragana_text)

    # 2. Keystroke conversion
    convert_corpus_for_all_keymaps(
        corpus_file="data/corpus/source_hiragana.txt",
        keymaps_dir=keymaps_dir,
        output_dir=generated_dir,
        chords_output_dir=chords_dir
    )

    results_a = []
    results_b = []

    # 3. Evaluation
    analyzer_a = KeyboardAnalyzer()
    analyzer_b = FluencyAnalyzerB()

    for filename in keymap_files:
        layout_id = filename[:-5]
        keymap_path = os.path.join(keymaps_dir, filename)
        romaji_table = "data/romaji_tables/azik.json" if "azik" in layout_id.lower() and os.path.exists("data/romaji_tables/azik.json") else "data/romaji_tables/standard_romaji.json"

        converter = LayoutConverter(keymap_path, romaji_table)
        disp_name = converter.name or layout_id

        # NeoJ-A (Physical Workload)
        if mode in ("a", "all"):
            stroke_file = os.path.join(generated_dir, f"{layout_id}.source.txt")
            chord_file = os.path.join(chords_dir, f"{layout_id}.source.txt")
            if os.path.exists(stroke_file):
                with open(stroke_file, "r", encoding="utf-8") as f:
                    keystrokes = f.read()
                chord_count = 0
                if os.path.exists(chord_file):
                    with open(chord_file, "r", encoding="utf-8") as f:
                        chord_count = f.read().count("(")
                res_a = analyzer_a.analyze_keystrokes(
                    layout_name=disp_name,
                    keystrokes=keystrokes,
                    chord_count=chord_count,
                    base_char_count=base_char_count
                )
                results_a.append(res_a)

        # NeoJ-B (Fluency & Awkwardness)
        if mode in ("b", "all"):
            res_b = analyzer_b.analyze_layout_corpus(
                layout_id=layout_id,
                layout_name=disp_name,
                converter=converter,
                word_corpus=word_corpus
            )
            results_b.append(res_b)

    composite_results = None
    if mode == "all" and results_a and results_b:
        composite_results = CompositeAnalyzer.evaluate_composite(results_a, results_b)

    # 4. Display Results
    reporter = BenchmarkReporter()
    reporter.print_results_table(
        results_a=results_a,
        results_b=results_b if mode in ("b", "all") else None,
        composite_results=composite_results
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Japanese Keyboard Layout Benchmark Tool")
    parser.add_argument(
        "--mode",
        choices=["a", "b", "all"],
        default="all",
        help="Evaluation mode: 'a' (Physical Effort), 'b' (Fluency & Strain), 'all' (Both & Composite)"
    )
    parser.add_argument(
        "--keymaps-dir",
        default="data/keymaps",
        help="Directory containing keymap JSON definitions (default: data/keymaps)"
    )
    args = parser.parse_args()

    run_benchmark(
        keymaps_dir=args.keymaps_dir,
        mode=args.mode
    )
