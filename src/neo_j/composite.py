"""
NeoJ Composite Quality Analyzer.
Synthesizes:
1. Physical Workload (Actuation, travel, reach, SFB strain)
2. Sync-Aware Timing Load (Simultaneous chord synchronization cost)
3. Typing Fluency & Word Comfort (Scissors, SFB/DSFB, roll flow, bottleneck word distribution)
"""
from typing import List, Dict, Tuple, Optional
from tabulate import tabulate

from .analyzer import LayoutAnalysisResult
from .analyzer_b import LayoutAnalysisResultB

class CompositeResult:
    def __init__(
        self,
        layout_name: str,
        pure_effort_per_char: float,
        sync_effort_per_char: float,
        fluency_score: float,
        pure_score: float,
        sync_score: float,
        composite_score: float,
        raw_result_a: Optional[LayoutAnalysisResult] = None,
        raw_result_b: Optional[LayoutAnalysisResultB] = None
    ):
        self.layout_name = layout_name
        self.pure_effort_per_char = pure_effort_per_char
        self.sync_effort_per_char = sync_effort_per_char
        self.fluency_score = fluency_score
        self.pure_score = pure_score
        self.sync_score = sync_score
        self.composite_score = composite_score
        self.raw_result_a = raw_result_a
        self.raw_result_b = raw_result_b

class CompositeAnalyzer:
    """Calculates composite typing score (0 - 100 pt) using geometric mean of physical and fluency pillars."""

    EFFORT_IDEAL_BOUND = 1.0
    EFFORT_HEAVY_BOUND = 3.0

    @classmethod
    def evaluate_composite(
        cls,
        results_a: List[LayoutAnalysisResult],
        results_b: List[LayoutAnalysisResultB]
    ) -> List[CompositeResult]:
        b_dict = {r.layout_name: r for r in results_b}
        composite_list = []

        for ra in results_a:
            rb = b_dict.get(ra.layout_name)
            if not rb:
                continue

            e_pure = ra.pure_effort_per_char
            e_sync = ra.sync_effort_per_char
            s_fluency = rb.fluency_score

            # Absolute Physical Efficiency Score (0-100 pt)
            s_pure = 100.0 * (1.0 - (e_pure - cls.EFFORT_IDEAL_BOUND) / (cls.EFFORT_HEAVY_BOUND - cls.EFFORT_IDEAL_BOUND))
            s_pure = max(0.0, min(100.0, s_pure))

            # Absolute Sync-Aware Score (0-100 pt)
            s_sync = 100.0 * (1.0 - (e_sync - cls.EFFORT_IDEAL_BOUND) / (cls.EFFORT_HEAVY_BOUND - cls.EFFORT_IDEAL_BOUND))
            s_sync = max(0.0, min(100.0, s_sync))

            # 3-Pillar Geometric Mean
            s_pure_safe = max(0.1, s_pure)
            s_sync_safe = max(0.1, s_sync)
            s_fluency_safe = max(0.1, s_fluency)
            total_score = (s_pure_safe * s_sync_safe * s_fluency_safe) ** (1.0 / 3.0)

            if s_pure <= 0.2 and s_sync <= 0.2 and s_fluency <= 0.2:
                total_score = 0.0

            composite_list.append(
                CompositeResult(
                    layout_name=ra.layout_name,
                    pure_effort_per_char=e_pure,
                    sync_effort_per_char=e_sync,
                    fluency_score=s_fluency,
                    pure_score=s_pure,
                    sync_score=s_sync,
                    composite_score=total_score,
                    raw_result_a=ra,
                    raw_result_b=rb
                )
            )

        return composite_list
