from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisSection:
    key: str
    title: str
    summary: str


@dataclass(frozen=True)
class ReportAnalysis:
    zone_title: str
    period_label: str | None
    sections: tuple[AnalysisSection, ...]

    def to_template_context(self) -> dict[str, str]:
        return {section.key: section.summary.rstrip().rstrip(".") for section in self.sections}
