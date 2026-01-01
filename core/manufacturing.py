"""
Lightweight manufacturing utilities for smoke tests.

This module provides a placeholder GCodeWriter so that CI can
produce hot-wire output files even when full post-processing
logic is not yet implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

import cadquery as cq


@dataclass
class GCodeWriter:
    """Minimal hot-wire G-code writer.

    The output is a diagnostic representation of the supplied
    root and tip profiles so smoke tests can validate pipeline
    wiring without requiring full CNC logic.
    """

    root_profile: cq.Wire
    tip_profile: cq.Wire
    kerf_offset: float
    feed_rate: float

    def _sample_points(self, profile: cq.Wire) -> Sequence[tuple[float, float, float]]:
        return [
            (vertex.X, vertex.Y, vertex.Z)
            for vertex in profile.Vertices()
        ]

    def _emit_profile(self, label: str, vertices: Iterable[tuple[float, float, float]]) -> str:
        lines = [f"; {label} profile"]
        for x, y, z in vertices:
            lines.append(f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f}")
        return "\n".join(lines)

    def write(self, target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)

        root_vertices = self._sample_points(self.root_profile)
        tip_vertices = self._sample_points(self.tip_profile)

        header = "\n".join(
            [
                "; Open-EZ hot-wire placeholder", # pragma: no cover - formatting only
                f"; Generated {datetime.utcnow().isoformat()}Z",
                f"; Kerf offset: {self.kerf_offset:.3f} in",
                f"; Feed rate: {self.feed_rate:.3f} in/min",
                "G21  ; metric units",
                f"F{self.feed_rate * 25.4:.2f}",
            ]
        )

        body = "\n\n".join(
            [
                self._emit_profile("Root", root_vertices),
                self._emit_profile("Tip", tip_vertices),
            ]
        )

        target.write_text(header + "\n\n" + body + "\n")
        return target
