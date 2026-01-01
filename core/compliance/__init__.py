"""
Open-EZ PDE: FAA Compliance Engine
==================================

ComplianceTracker: Automates FAA Form 8000-38 credit tally.
Ensures amateur-built status per 14 CFR Part 21.191(g).

The system generates FABRICATION AIDS, not finished parts.
Builder must operate CNC equipment and perform all layups manually.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import json

from config import config


class ManufacturingMethod(Enum):
    """Methods for fabricating aircraft components."""

    BUILDER_MANUAL = "builder_manual"           # Hand layup, hand cutting
    BUILDER_CNC = "builder_cnc"                 # Builder operates CNC
    BUILDER_HELPER = "builder_helper"           # Helper assists under builder supervision
    COMMERCIAL_KIT = "commercial_kit"           # Pre-fab kit parts
    COMMERCIAL_SERVICE = "commercial_service"   # Outsourced fabrication


class CreditCategory(Enum):
    """FAA Form 8000-38 credit categories."""
    FABRICATION = "fabrication"     # Making parts from raw materials
    ASSEMBLY = "assembly"           # Joining pre-made parts


@dataclass
class BuildTask:
    """Individual task in the build process."""
    task_id: str
    description: str
    category: CreditCategory
    base_credit: float              # Credit weight (0.0 to 1.0)
    method: ManufacturingMethod = ManufacturingMethod.BUILDER_MANUAL
    completed: bool = False
    completion_date: Optional[datetime] = None
    notes: str = ""
    photo_paths: List[str] = field(default_factory=list)

    @property
    def builder_credit(self) -> float:
        """
        Calculate builder credit based on method.

        Manual and builder-operated CNC get full credit.
        Commercial services get reduced or zero credit.
        """
        if not self.completed:
            return 0.0

        if self.method in (ManufacturingMethod.BUILDER_MANUAL,
                           ManufacturingMethod.BUILDER_CNC):
            return self.base_credit

        if self.method == ManufacturingMethod.BUILDER_HELPER:
            # Helper-assisted work gets partial credit; builder must still
            # direct and operate tools to satisfy the FAA "major portion" rule.
            return self.base_credit * 0.5

        if self.method == ManufacturingMethod.COMMERCIAL_KIT:
            return self.base_credit * 0.5  # Reduced credit for kits

        return 0.0  # No credit for outsourced work


class ComplianceTracker:
    """
    Tracks FAA 51% Rule compliance throughout the build.

    Maintains a digital "traveler" that:
    - Lists all fabrication and assembly tasks
    - Tracks manufacturing method for each
    - Calculates running builder credit total
    - Generates FAA Form 8000-38 report
    """

    # Required threshold for amateur-built status
    REQUIRED_CREDIT = 0.51

    def __init__(self):
        """Initialize tracker with standard Long-EZ tasks."""
        self._tasks: Dict[str, BuildTask] = {}
        self._init_standard_tasks()

    def _init_standard_tasks(self) -> None:
        """Populate with standard Long-EZ build tasks from config."""
        # Map config task credits to BuildTask objects
        task_definitions = [
            # Wing fabrication
            ("wing_cores_left", "Fabricate left wing foam cores",
             CreditCategory.FABRICATION, config.compliance.task_credits.get("wing_cores_cnc", 0.04)),
            ("wing_cores_right", "Fabricate right wing foam cores",
             CreditCategory.FABRICATION, config.compliance.task_credits.get("wing_cores_cnc", 0.04)),
            ("wing_skins_left", "Layup left wing fiberglass skins",
             CreditCategory.FABRICATION, config.compliance.task_credits.get("wing_skins_layup", 0.06)),
            ("wing_skins_right", "Layup right wing fiberglass skins",
             CreditCategory.FABRICATION, config.compliance.task_credits.get("wing_skins_layup", 0.06)),

            # Canard fabrication
            ("canard_cores", "Fabricate canard foam cores (Roncz R1145MS)",
             CreditCategory.FABRICATION, 0.05),
            ("canard_skins", "Layup canard fiberglass skins",
             CreditCategory.FABRICATION, 0.05),

            # Fuselage fabrication
            ("fuselage_bulkheads", "Fabricate fuselage bulkheads (F22, F28, etc.)",
             CreditCategory.FABRICATION, 0.06),
            ("fuselage_sides", "Layup fuselage side panels",
             CreditCategory.FABRICATION, 0.05),
            ("fuselage_bottom", "Layup fuselage bottom",
             CreditCategory.FABRICATION, 0.04),

            # Fuselage assembly
            ("fuselage_assembly", "Assemble fuselage structure (boxing)",
             CreditCategory.ASSEMBLY, config.compliance.task_credits.get("fuselage_assembly", 0.08)),

            # Control system
            ("control_surfaces", "Fabricate ailerons and elevators",
             CreditCategory.FABRICATION, 0.04),
            ("control_linkages", "Install control linkages and cables",
             CreditCategory.ASSEMBLY, config.compliance.task_credits.get("control_system", 0.04)),

            # Landing gear
            ("main_gear", "Fabricate main landing gear bow",
             CreditCategory.FABRICATION, 0.03),
            ("nose_gear", "Install nose gear assembly",
             CreditCategory.ASSEMBLY, 0.03),

            # Strakes (fuel tanks)
            ("strake_cores", "Fabricate strake foam cores",
             CreditCategory.FABRICATION, 0.04),
            ("strake_skins", "Layup strake skins and baffles",
             CreditCategory.FABRICATION, 0.04),

            # Engine installation
            ("engine_mount", "Fabricate/install engine mount",
             CreditCategory.ASSEMBLY, 0.03),
            ("engine_baffles", "Fabricate engine baffles",
             CreditCategory.FABRICATION, 0.02),

            # Electrical
            ("wiring_harness", "Fabricate and install wiring harness",
             CreditCategory.ASSEMBLY, config.compliance.task_credits.get("electrical", 0.04)),

            # Finishing
            ("surface_prep", "Sand and prepare surfaces",
             CreditCategory.FABRICATION, 0.03),
            ("paint", "Apply paint/finish",
             CreditCategory.FABRICATION, 0.03),

            # Final assembly
            ("systems_integration", "Final systems integration and testing",
             CreditCategory.ASSEMBLY, config.compliance.task_credits.get("final_assembly", 0.10)),
        ]

        for task_id, description, category, credit in task_definitions:
            self._tasks[task_id] = BuildTask(
                task_id=task_id,
                description=description,
                category=category,
                base_credit=credit
            )

    def get_task(self, task_id: str) -> BuildTask:
        """Get a task by ID."""
        if task_id not in self._tasks:
            raise ValueError(f"Unknown task: {task_id}")
        return self._tasks[task_id]

    def complete_task(
        self,
        task_id: str,
        method: ManufacturingMethod,
        notes: str = "",
        photo_paths: Optional[List[str]] = None
    ) -> None:
        """
        Mark a task as completed.

        Args:
            task_id: Task identifier
            method: How the task was accomplished
            notes: Builder's notes
            photo_paths: Paths to documentation photos
        """
        task = self.get_task(task_id)
        task.completed = True
        task.completion_date = datetime.now()
        task.method = method
        task.notes = notes
        task.photo_paths = photo_paths or []

    @property
    def total_credit(self) -> float:
        """Calculate total builder credit from completed tasks."""
        return sum(task.builder_credit for task in self._tasks.values())

    @property
    def is_compliant(self) -> bool:
        """Check if build meets 51% requirement."""
        return self.total_credit >= self.REQUIRED_CREDIT

    @property
    def remaining_credit_needed(self) -> float:
        """Calculate how much more credit is needed for compliance."""
        return max(0.0, self.REQUIRED_CREDIT - self.total_credit)

    def get_incomplete_tasks(self) -> List[BuildTask]:
        """Get list of tasks not yet completed."""
        return [t for t in self._tasks.values() if not t.completed]

    def get_completed_tasks(self) -> List[BuildTask]:
        """Get list of completed tasks."""
        return [t for t in self._tasks.values() if t.completed]

    def generate_report(self) -> str:
        """
        Generate FAA Form 8000-38 style report.

        Returns:
            Markdown-formatted compliance report
        """
        completed = self.get_completed_tasks()
        incomplete = self.get_incomplete_tasks()

        report = f"""
# FAA Amateur-Built Compliance Report
## Open-EZ PDE - Form 8000-38 Credit Summary

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Aircraft: {config.project_name} ({config.baseline})

---

## Summary

| Metric | Value |
|--------|-------|
| Total Builder Credit | {self.total_credit:.1%} |
| Required Threshold | {self.REQUIRED_CREDIT:.0%} |
| Status | {'**COMPLIANT**' if self.is_compliant else '**NOT YET COMPLIANT**'} |
| Tasks Completed | {len(completed)} / {len(self._tasks)} |

---

## Completed Tasks

| Task | Category | Method | Credit |
|------|----------|--------|--------|
"""
        for task in completed:
            report += f"| {task.description} | {task.category.value} | {task.method.value} | {task.builder_credit:.1%} |\n"

        report += f"""
---

## Remaining Tasks

| Task | Category | Potential Credit |
|------|----------|-----------------|
"""
        for task in incomplete:
            report += f"| {task.description} | {task.category.value} | {task.base_credit:.1%} |\n"

        report += f"""
---

## Notes

- All CNC operations must be **builder-operated** to receive full credit.
- Fiberglass layups are inherently manual and receive full fabrication credit.
- The PDE generates **fabrication aids** (G-code, templates), not finished parts.
- Photo documentation of each task is recommended for DAR inspection.

---

*Generated by Open-EZ PDE Compliance Engine*
"""
        return report

    def export_json(self, output_path: Path) -> Path:
        """
        Export compliance data as JSON for backup/integration.

        Args:
            output_path: Directory for JSON output

        Returns:
            Path to JSON file
        """
        data = {
            "project": config.project_name,
            "version": config.version,
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_credit": self.total_credit,
                "required": self.REQUIRED_CREDIT,
                "compliant": self.is_compliant,
            },
            "tasks": [
                {
                    "id": t.task_id,
                    "description": t.description,
                    "category": t.category.value,
                    "base_credit": t.base_credit,
                    "method": t.method.value if t.completed else None,
                    "completed": t.completed,
                    "completion_date": t.completion_date.isoformat() if t.completion_date else None,
                    "builder_credit": t.builder_credit,
                    "notes": t.notes,
                    "photos": t.photo_paths,
                }
                for t in self._tasks.values()
            ]
        }

        json_file = output_path / "compliance_tracker.json"
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)

        return json_file


# Module-level tracker instance
compliance_tracker = ComplianceTracker()

# Task checklist/credit mapping helper
from .tracker import ComplianceTaskTracker, TaskRole, compliance_task_tracker  # noqa: E402,F401
