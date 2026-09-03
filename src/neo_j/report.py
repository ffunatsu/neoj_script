"""
Benchmark Output Formatter for Keyboard Layout Evaluations.
Displays evaluation metrics and scores in clean tables without marketing rhetoric.
"""
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import box

from .analyzer import LayoutAnalysisResult
from .analyzer_b import LayoutAnalysisResultB
from .composite import CompositeResult

class BenchmarkReporter:
    def __init__(self):
        self.console = Console(width=120)

    def print_results_table(
        self,
        results_a: List[LayoutAnalysisResult],
        results_b: Optional[List[LayoutAnalysisResultB]] = None,
        composite_results: Optional[List[CompositeResult]] = None
    ):
        """Print evaluated layouts and their metrics in a clean table."""
        if not results_a:
            self.console.print("[yellow]評価対象の配列データがありません。[/yellow]")
            return

        b_map = {r.layout_name: r for r in (results_b or [])}
        comp_map = {r.layout_name: r for r in (composite_results or [])}

        table = Table(
            title="配列評価結果一覧",
            box=box.SIMPLE_HEAVY,
            header_style="bold",
            show_lines=False,
            expand=False
        )

        table.add_column("配列名", style="cyan", justify="left", no_wrap=True)
        table.add_column("打鍵負荷\n(Effort/字)", justify="right")
        table.add_column("打鍵数/字\n(打/字)", justify="right")
        table.add_column("総移動距離\n(cm)", justify="right")
        table.add_column("SFB率\n(%)", justify="right")
        table.add_column("交互打鍵率\n(%)", justify="right")

        if results_b:
            table.add_column("流暢度スコア\n(0-100)", justify="right")
            table.add_column("快適単語率\n(%)", justify="right")
            table.add_column("ハサミ討ち率\n(回/100語)", justify="right")

        if composite_results:
            table.add_column("総合スコア\n(0-100)", justify="right", style="bold green")

        for ra in results_a:
            row = [
                ra.layout_name,
                f"{ra.pure_effort_per_char:.3f}",
                f"{(ra.num_keys / 1097.0):.2f}" if ra.num_keys else "-",
                f"{ra.total_distance_cm:.1f}",
                f"{ra.sfb_rate_pct:.2f}%",
                f"{ra.hand_alternation_rate_pct:.1f}%",
            ]

            if results_b:
                rb = b_map.get(ra.layout_name)
                if rb:
                    row.extend([
                        f"{rb.fluency_score:.1f}",
                        f"{rb.smooth_words_ratio_pct:.1f}%",
                        f"{(rb.severe_scissors_rate + rb.mild_scissors_rate):.1f}",
                    ])
                else:
                    row.extend(["-", "-", "-"])

            if composite_results:
                rc = comp_map.get(ra.layout_name)
                if rc:
                    row.append(f"{rc.composite_score:.1f}")
                else:
                    row.append("-")

            table.add_row(*row)

        self.console.print()
        self.console.print(table)
        self.console.print()
