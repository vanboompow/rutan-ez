"""
Open-EZ PDE: Weight & Balance
==============================

Provides WeightItem and WeightBalance data classes for centre-of-gravity
calculations.  These were previously embedded in core/analysis.py.

Backward compatibility: ``from core.analysis import WeightItem, WeightBalance``
still works because analysis.py re-exports both names.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class WeightItem:
    """Single weight component for W&B calculations."""

    name: str
    weight: float  # pounds
    arm: float  # inches from datum (FS)
    category: str = "fixed"  # fixed, fuel, payload

    @property
    def moment(self) -> float:
        return self.weight * self.arm


@dataclass
class WeightBalance:
    """Complete weight and balance calculation."""

    items: List[WeightItem] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(item.weight for item in self.items)

    @property
    def total_moment(self) -> float:
        return sum(item.moment for item in self.items)

    @property
    def cg_location(self) -> float:
        if self.total_weight == 0:
            return 0.0
        return self.total_moment / self.total_weight

    def add_item(self, name: str, weight: float, arm: float, category: str = "fixed"):
        self.items.append(WeightItem(name, weight, arm, category))

    def summary(self) -> str:
        lines = ["Weight & Balance Summary", "=" * 40]
        lines.append(f"{'Item':<25} {'Weight':>8} {'Arm':>8} {'Moment':>10}")
        lines.append("-" * 40)

        for item in self.items:
            lines.append(
                f"{item.name:<25} {item.weight:>8.1f} {item.arm:>8.1f} {item.moment:>10.1f}"
            )

        lines.append("-" * 40)
        lines.append(
            f"{'TOTAL':<25} {self.total_weight:>8.1f} {self.cg_location:>8.1f} {self.total_moment:>10.1f}"
        )
        lines.append("")
        lines.append(f"Center of Gravity: {self.cg_location:.2f} in (FS)")

        return "\n".join(lines)


__all__ = ["WeightItem", "WeightBalance"]
