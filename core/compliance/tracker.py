"""
Compliance task tracker bridging CAD/G-code generation to FAA 8000-38 credits.

The PDE emits fabrication aids. This module records which artifacts were
produced by the builder vs. a helper and renders a running Markdown checklist
for DAR/FAA inspections.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from config import config
from . import ComplianceTracker, ManufacturingMethod, compliance_tracker


class TaskRole(Enum):
    """Who performed the task for FAA credit attribution."""

    BUILDER = "builder"
    HELPER = "helper"


@dataclass
class ChecklistEntry:
    """One line item tying an artifact back to FAA task credit."""

    task_id: str
    description: str
    artifact: str
    component: str
    role: TaskRole
    method: ManufacturingMethod
    completed: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    note: str = ""
    credit_awarded: float = 0.0


class ComplianceTaskTracker:
    """
    Map generated artifacts to FAA Form 8000-38 task credits and emit checklists.

    The mapping enforces builder-operated Roncz canard work as default while
    still distinguishing helper-assisted work for partial credit.
    """

    # Map (component, artifact) -> [(task_id, default_method)]
    ARTIFACT_TASK_MAP: Dict[Tuple[str, str], List[Tuple[str, ManufacturingMethod]]] = {
        ("canard", "cad"): [
            ("canard_cores", ManufacturingMethod.BUILDER_CNC),
        ],
        ("canard", "layup_schedule"): [
            ("canard_skins", ManufacturingMethod.BUILDER_MANUAL),
        ],
        ("wing", "cad"): [
            ("wing_cores_left", ManufacturingMethod.BUILDER_CNC),
            ("wing_cores_right", ManufacturingMethod.BUILDER_CNC),
        ],
        ("wing", "layup_schedule"): [
            ("wing_skins_left", ManufacturingMethod.BUILDER_MANUAL),
            ("wing_skins_right", ManufacturingMethod.BUILDER_MANUAL),
        ],
    }

    def __init__(self, tracker: ComplianceTracker):
        self._tracker = tracker
        self._checklist: List[ChecklistEntry] = []

    @property
    def checklist(self) -> List[ChecklistEntry]:
        """Return recorded checklist entries."""

        return list(self._checklist)

    def _task_ids(self) -> Iterable[str]:
        """All task IDs linked to artifact generation."""

        for bindings in self.ARTIFACT_TASK_MAP.values():
            for task_id, _ in bindings:
                yield task_id

    def record_generation(
        self,
        component: str,
        artifact: str,
        role: TaskRole = TaskRole.BUILDER,
        note: str = "",
    ) -> List[ChecklistEntry]:
        """
        Record that an artifact was generated and update compliance credits.

        Args:
            component: Component name (e.g., "canard", "wing")
            artifact: Artifact type (e.g., "cad", "layup_schedule")
            role: Who operated the tool or performed the work
            note: Optional note for documentation
        """

        bindings = self.ARTIFACT_TASK_MAP.get((component, artifact), [])
        entries: List[ChecklistEntry] = []

        for task_id, method in bindings:
            credit_method = method
            if role == TaskRole.HELPER and method in (
                ManufacturingMethod.BUILDER_MANUAL,
                ManufacturingMethod.BUILDER_CNC,
            ):
                credit_method = ManufacturingMethod.BUILDER_HELPER

            task = self._tracker.get_task(task_id)

            if not task.completed:
                self._tracker.complete_task(
                    task_id,
                    credit_method,
                    notes=note or f"{artifact} generated for {component}",
                )
            else:
                task.method = credit_method
                if note:
                    task.notes = note

            updated_task = self._tracker.get_task(task_id)

            entry = ChecklistEntry(
                task_id=task_id,
                description=updated_task.description,
                artifact=artifact,
                component=component,
                role=role,
                method=credit_method,
                completed=True,
                note=note,
                credit_awarded=updated_task.builder_credit,
            )
            self._checklist.append(entry)
            entries.append(entry)

        return entries

    def render_running_checklist(self) -> str:
        """Render a Markdown checklist for tracked tasks."""

        latest: Dict[str, ChecklistEntry] = {}
        for entry in self._checklist:
            latest[entry.task_id] = entry

        header = f"""
# FAA 8000-38 Running Checklist
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
Project: {config.project_name} ({config.baseline})
Baseline Canard Airfoil: {config.airfoils.canard.value}

| Task | Artifact | Role | Method | Status | Credit |
|------|----------|------|--------|--------|--------|
"""

        rows = []
        for task_id in sorted(set(self._task_ids())):
            task = self._tracker.get_task(task_id)
            entry = latest.get(task_id)
            status = "DONE" if task.completed else "PENDING"
            artifact = entry.artifact if entry else "—"
            role = entry.role.value if entry else TaskRole.BUILDER.value
            method = (
                entry.method.value
                if entry
                else (task.method.value if task.completed else "builder_manual")
            )
            credit = task.builder_credit if task.completed else task.base_credit

            rows.append(
                f"| {task.description} | {artifact} | {role} | {method} | "
                f"{status} | {credit:.1%} |"
            )

        return header + "\n".join(rows) + "\n"

    def write_checklist(self, output_path: Path) -> Path:
        """Write the running checklist to disk."""

        output_path.mkdir(parents=True, exist_ok=True)
        checklist_file = output_path / "compliance_checklist.md"
        checklist_file.write_text(self.render_running_checklist())
        return checklist_file

    def write_layup_schedule(self, component: str, output_path: Path) -> Path:
        """Generate a Markdown layup schedule to accompany CAD/G-code."""

        output_path.mkdir(parents=True, exist_ok=True)

        if component not in ("canard", "wing"):
            raise ValueError("Layup schedules currently supported for canard and wing")

        if component == "canard":
            skin_task = "canard_skins"
            header = "Roncz R1145MS Canard Layup"
            steps = [
                ("Surface prep", "Sand/clean foam cores, apply micro slurry."),
                (
                    "Top skin layup",
                    "Apply 2 plies BID at ±45°, ensure fiber bias over span; squeegee to 50% resin content.",
                ),
                (
                    "Bottom skin layup",
                    "Repeat 2 plies BID at ±45°; peel-ply hinge line and spar cap step.",
                ),
                (
                    "Shear web cure",
                    "Install peel-ply and allow full cure before trimming trailing edge.",
                ),
            ]
        else:
            skin_task = "wing_skins_left"
            header = "Main Wing Layup"
            steps = [
                (
                    "Spar cap build",
                    f"Lay {config.materials.spar_cap_plies} UNI plies in trough, maintaining {config.materials.spar_trough_depth:.3f}\" depth.",
                ),
                (
                    "Upper skin",
                    "BID at ±45° across panel; stagger overlaps by at least 1 in.",
                ),
                (
                    "Lower skin",
                    "Mirror upper skin schedule; peel-ply control surface seams.",
                ),
                (
                    "Post-cure",
                    "Maintain 140°F post-cure per epoxy data sheet before cutting control surfaces.",
                ),
            ]

        lines = [
            f"# {header}",
            "",
            "Builder of record must perform the following layups to retain FAA builder credit.",
            "",
            "| Step | Action | Operator | Credit Task |",
            "|------|--------|----------|-------------|",
        ]

        task = self._tracker.get_task(skin_task)
        for idx, (title, action) in enumerate(steps, start=1):
            lines.append(
                f"| {idx} | {title}: {action} | BUILDER | {task.description} ({task.base_credit:.1%}) |"
            )

        lines.extend(
            [
                "",
                "- Ensure builder name appears on shop traveler for each layup.",
                "- Helper-assisted work must be documented; credit is reduced automatically.",
                "- Attach photos of peel-ply removal and cured surfaces to the compliance package.",
            ]
        )

        layup_file = output_path / f"{component}_layup_schedule.md"
        layup_file.write_text("\n".join(lines) + "\n")
        return layup_file


# Module-level helper bound to the primary compliance tracker
compliance_task_tracker = ComplianceTaskTracker(compliance_tracker)


