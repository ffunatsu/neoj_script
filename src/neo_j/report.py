"""
Benchmark Output Formatter for Keyboard Layout Evaluations.
Displays evaluation metrics, scores, and word diagnostics (best/worst words) in clean tables.
"""
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import box

from .analyzer import LayoutAnalysisResult
from .analyzer_b import LayoutAnalysisResultB, WordAnalysisResult
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
        """Print evaluated layouts and their summary metrics in a clean table."""
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

    def print_words_diagnostics(self, results_b: List[LayoutAnalysisResultB]):
        """Print top 10 easiest (best) and hardest (worst) words for each evaluated layout."""
        if not results_b:
            return

        for r in results_b:
            self.console.print(f"[bold cyan]■ {r.layout_name}[/bold cyan] （流暢度スコア: [bold green]{r.fluency_score:.1f}[/bold green] / 快適単語率: [bold magenta]{r.smooth_words_ratio_pct:.1f}%[/bold magenta]）")
            
            # 1. Best Words Table (打ちやすい単語 Top 10)
            table_best = Table(
                title=f"✨ 最も打ちやすい単語 Top 10 ({r.layout_name})",
                box=box.ROUNDED,
                header_style="bold green",
                show_lines=False
            )
            table_best.add_column("No", justify="center", style="dim")
            table_best.add_column("単語", style="bold")
            table_best.add_column("打鍵列 (QWERTY)", style="cyan")
            table_best.add_column("難易度", justify="right")
            table_best.add_column("最大負荷", justify="right")
            table_best.add_column("快適な理由・運指特性", style="white")

            for i, w in enumerate(r.best_words[:10], 1):
                reason = w.pleasant_reason_desc if w.pleasant_reason_desc else "段交差なし・軽快リズム運指"
                table_best.add_row(
                    str(i),
                    w.word,
                    w.keystrokes_repr,
                    f"{w.difficulty_score:.2f}",
                    f"{w.peak_strain:.2f}",
                    reason
                )

            self.console.print(table_best)

            # 2. Worst Words Table (打ちにくい単語 Top 10)
            table_worst = Table(
                title=f"⚠️ 最も打ちにくい単語 Top 10 ({r.layout_name})",
                box=box.ROUNDED,
                header_style="bold red",
                show_lines=False
            )
            table_worst.add_column("No", justify="center", style="dim")
            table_worst.add_column("単語", style="bold")
            table_worst.add_column("打鍵列 (QWERTY)", style="cyan")
            table_worst.add_column("難易度", justify="right")
            table_worst.add_column("最大負荷", justify="right")
            table_worst.add_column("主な不快原因・ボトルネック遷移", style="yellow")

            for i, w in enumerate(r.worst_words[:10], 1):
                table_worst.add_row(
                    str(i),
                    w.word,
                    w.keystrokes_repr,
                    f"{w.difficulty_score:.2f}",
                    f"{w.peak_strain:.2f}",
                    w.worst_transition_desc
                )

            self.console.print(table_worst)
            self.console.print()
