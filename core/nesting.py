"""Nesting and CAM prep utilities.

Provides a lightweight bin-packing optimizer that ingests DXF outlines,
places them on available stock sheets, and emits nested DXFs plus a CSV
manifest suitable for CAM import. Post-processing adds dogbones/fillets
and label engraving layers to preserve cut ordering.

Grain Orientation Support:
- For plywood parts, face grain should align with primary load path
- For foam sheets, cell elongation direction affects bending stiffness
- Grain constraints can be NONE, PARALLEL, PERPENDICULAR, or SPECIFIC angle
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import ezdxf
from ezdxf import bbox


class GrainConstraint(Enum):
    """Material grain/fiber orientation constraints."""

    NONE = "none"  # No grain constraint
    PARALLEL = "parallel"  # Grain must align with part length (0°)
    PERPENDICULAR = "perpendicular"  # Grain perpendicular to part length (90°)
    SPECIFIC = "specific"  # Specific angle required (see grain_angle)


@dataclass
class Outline:
    """Single part outline sourced from a DXF."""

    name: str
    source: Path
    width: float
    height: float
    quantity: int = 1
    laminate: Optional[str] = None

    # Grain/fiber orientation support
    grain_constraint: GrainConstraint = GrainConstraint.NONE
    grain_angle: float = 0.0  # Degrees from horizontal (for SPECIFIC constraint)
    primary_load_direction: float = 0.0  # Degrees - direction of primary load path


@dataclass
class Placement:
    """Placement of an outline on a specific sheet."""

    outline: Outline
    sheet_index: int
    origin: Tuple[float, float]
    rotation: float = 0.0  # Rotation applied during placement (degrees)

    @property
    def label_position(self) -> Tuple[float, float]:
        x0, y0 = self.origin
        if self.rotation == 90.0:
            return x0 + self.outline.height / 2, y0 + self.outline.width / 2
        return x0 + self.outline.width / 2, y0 + self.outline.height / 2

    @property
    def placed_width(self) -> float:
        """Width after rotation is applied."""
        if self.rotation == 90.0:
            return self.outline.height
        return self.outline.width

    @property
    def placed_height(self) -> float:
        """Height after rotation is applied."""
        if self.rotation == 90.0:
            return self.outline.width
        return self.outline.height

    @property
    def grain_direction_on_sheet(self) -> float:
        """Compute the grain direction after placement rotation."""
        base_angle = self.outline.grain_angle
        return (base_angle + self.rotation) % 180.0

    @property
    def grain_note(self) -> str:
        """Human-readable grain direction note for operator."""
        if self.outline.grain_constraint == GrainConstraint.NONE:
            return "No constraint"
        direction = self.grain_direction_on_sheet
        if abs(direction) < 5 or abs(direction - 180) < 5:
            return "Grain horizontal (0°)"
        elif abs(direction - 90) < 5:
            return "Grain vertical (90°)"
        else:
            return f"Grain at {direction:.1f}°"


class NestingPlanner:
    """Performs simple shelf-based nesting for DXF outlines.

    Enhanced with grain orientation support:
    - Respects grain constraints when placing parts
    - May rotate parts 90° to fit constraints
    - Adds grain direction arrows to output DXF
    """

    def __init__(
        self,
        stock_sheets: List[Tuple[float, float]],
        margin: float = 0.25,
        spacing: float = 0.125,
        dogbone_radius: float = 0.0,
        fillet_radius: float = 0.0,
        sheet_grain_direction: float = 0.0,  # Sheet grain runs horizontal (0°)
    ):
        self.stock_sheets = stock_sheets
        self.margin = margin
        self.spacing = spacing
        self.dogbone_radius = dogbone_radius
        self.fillet_radius = fillet_radius
        self.sheet_grain_direction = sheet_grain_direction

    def load_outlines(
        self, directory: Path, laminate: Optional[str] = None
    ) -> List[Outline]:
        """Load DXF outlines from a directory and compute extents."""

        outlines: List[Outline] = []
        for path in sorted(directory.glob("*.dxf")):
            try:
                doc = ezdxf.readfile(path)
            except IOError:
                continue
            extents = bbox.extents(doc.modelspace())
            if not extents:
                continue
            (min_x, min_y, _), (max_x, max_y, _) = extents
            outlines.append(
                Outline(
                    name=path.stem,
                    source=path,
                    width=max_x - min_x,
                    height=max_y - min_y,
                    laminate=laminate,
                )
            )
        return outlines

    def _compute_required_rotation(self, outline: Outline) -> float:
        """
        Compute required rotation to satisfy grain constraint.

        Returns rotation in degrees (0 or 90) that aligns the part's
        primary load direction with the sheet grain direction.
        """
        if outline.grain_constraint == GrainConstraint.NONE:
            return 0.0

        # For PARALLEL: part's primary load direction should match sheet grain
        # For PERPENDICULAR: part's primary load should be 90° from sheet grain
        # For SPECIFIC: use the specified grain_angle

        if outline.grain_constraint == GrainConstraint.PARALLEL:
            target_angle = self.sheet_grain_direction
        elif outline.grain_constraint == GrainConstraint.PERPENDICULAR:
            target_angle = (self.sheet_grain_direction + 90.0) % 180.0
        elif outline.grain_constraint == GrainConstraint.SPECIFIC:
            target_angle = outline.grain_angle
        else:
            return 0.0

        # Compute angle difference
        diff = (target_angle - outline.primary_load_direction) % 180.0

        # Choose rotation: 0° or 90° to get closest to target
        if diff < 45 or diff > 135:
            return 0.0  # No rotation needed
        else:
            return 90.0  # Rotate 90°

    def pack(
        self,
        outlines: Iterable[Outline],
        respect_grain: bool = True,
    ) -> List[Placement]:
        """Greedy shelf packer across the configured stock sheets.

        Args:
            outlines: Parts to nest
            respect_grain: If True, rotate parts to satisfy grain constraints

        Returns:
            List of Placement objects
        """
        placements: List[Placement] = []
        sheet_index = 0
        sheet_w, sheet_h = self.stock_sheets[sheet_index]
        cursor_x = self.margin
        cursor_y = self.margin
        row_height = 0.0

        for outline in sorted(
            outlines, key=lambda o: max(o.width, o.height), reverse=True
        ):
            for _ in range(outline.quantity):
                # Compute rotation for grain constraint
                rotation = 0.0
                if respect_grain:
                    rotation = self._compute_required_rotation(outline)

                # Get dimensions after rotation
                if rotation == 90.0:
                    part_w, part_h = outline.height, outline.width
                else:
                    part_w, part_h = outline.width, outline.height

                # Move to next row if needed
                if cursor_x + part_w + self.margin > sheet_w:
                    cursor_x = self.margin
                    cursor_y += row_height + self.spacing
                    row_height = 0.0

                # Move to next sheet if vertical space is exhausted
                if cursor_y + part_h + self.margin > sheet_h:
                    sheet_index += 1
                    if sheet_index >= len(self.stock_sheets):
                        raise ValueError(
                            "Not enough stock sheets to place all outlines"
                        )
                    sheet_w, sheet_h = self.stock_sheets[sheet_index]
                    cursor_x = self.margin
                    cursor_y = self.margin
                    row_height = 0.0

                placements.append(
                    Placement(
                        outline=outline,
                        sheet_index=sheet_index,
                        origin=(cursor_x, cursor_y),
                        rotation=rotation,
                    )
                )
                cursor_x += part_w + self.spacing
                row_height = max(row_height, part_h)

        return placements

    def _copy_entities(
        self, source_doc: ezdxf.document.Drawing, target_msp, dx: float, dy: float
    ) -> None:
        for entity in source_doc.modelspace():
            copied = entity.copy()
            copied.translate(dx, dy, 0)
            target_msp.add_entity(copied)

    def _add_corner_relief(
        self, msp, placement: Placement, radius: float, layer: str
    ) -> None:
        if radius <= 0:
            return
        x0, y0 = placement.origin
        w, h = placement.outline.width, placement.outline.height
        corners = [
            (x0, y0),
            (x0 + w, y0),
            (x0 + w, y0 + h),
            (x0, y0 + h),
        ]
        for cx, cy in corners:
            msp.add_circle((cx, cy), radius, dxfattribs={"layer": layer})

    def _add_label(self, msp, placement: Placement, engraving_depth: float) -> None:
        cx, cy = placement.label_position
        msp.add_text(
            placement.outline.name,
            dxfattribs={"layer": "ENGRAVE_LABELS"},
        ).set_pos((cx, cy), align="MIDDLE_CENTER")
        msp.add_line(
            (cx, cy), (cx, cy - engraving_depth), dxfattribs={"layer": "ENGRAVE_LABELS"}
        )

    def export(
        self,
        placements: List[Placement],
        output_dir: Path,
        engraving_depth: float = 0.02,
        laminate_cut_orders: Optional[Dict[str, List[str]]] = None,
    ) -> Path:
        """Export nested DXFs by sheet and a CSV manifest."""

        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows: List[str] = ["sheet,part,x,y,width,height,laminate,cut_order"]

        grouped: Dict[int, List[Placement]] = {}
        for placement in placements:
            grouped.setdefault(placement.sheet_index, []).append(placement)

        for sheet_index, sheet_placements in grouped.items():
            doc = ezdxf.new()
            msp = doc.modelspace()
            sheet_w, sheet_h = self.stock_sheets[sheet_index]
            msp.add_lwpolyline(
                [
                    (0, 0),
                    (sheet_w, 0),
                    (sheet_w, sheet_h),
                    (0, sheet_h),
                ],
                close=True,
                dxfattribs={"layer": "STOCK"},
            )

            for placement in sheet_placements:
                src = ezdxf.readfile(placement.outline.source)
                self._copy_entities(src, msp, *placement.origin)
                self._add_corner_relief(msp, placement, self.dogbone_radius, "DOGBONE")
                self._add_corner_relief(msp, placement, self.fillet_radius, "FILLET")
                self._add_label(msp, placement, engraving_depth)

                cut_steps = (
                    laminate_cut_orders.get(placement.outline.laminate or "")
                    if laminate_cut_orders
                    else None
                )
                cut_order = " > ".join(cut_steps or ["ENGRAVE", "PROFILE"])

                manifest_rows.append(
                    ",".join(
                        [
                            str(sheet_index),
                            placement.outline.name,
                            f"{placement.origin[0]:.3f}",
                            f"{placement.origin[1]:.3f}",
                            f"{placement.outline.width:.3f}",
                            f"{placement.outline.height:.3f}",
                            placement.outline.laminate or "",
                            cut_order,
                        ]
                    )
                )

            doc.saveas(output_dir / f"nested_sheet_{sheet_index}.dxf")

        manifest_path = output_dir / "nest_manifest.csv"
        manifest_path.write_text("\n".join(manifest_rows))
        return manifest_path

    def _add_grain_arrow(
        self,
        msp,
        placement: Placement,
        arrow_length: float = 1.5,
    ) -> None:
        """
        Add grain direction arrow to indicate fiber/grain orientation.

        Draws an arrow showing the grain direction for the operator.
        For parts with no constraint, no arrow is drawn.
        """
        if placement.outline.grain_constraint == GrainConstraint.NONE:
            return

        cx, cy = placement.label_position
        angle_rad = math.radians(placement.grain_direction_on_sheet)

        # Arrow endpoints
        dx = arrow_length / 2 * math.cos(angle_rad)
        dy = arrow_length / 2 * math.sin(angle_rad)

        x1, y1 = cx - dx, cy - dy
        x2, y2 = cx + dx, cy + dy

        # Main arrow line
        msp.add_line(
            (x1, y1), (x2, y2),
            dxfattribs={"layer": "GRAIN_DIRECTION", "color": 3}  # Green
        )

        # Arrowhead
        head_size = 0.25
        head_angle = math.radians(150)  # 30° from arrow direction

        hx1 = x2 + head_size * math.cos(angle_rad + head_angle)
        hy1 = y2 + head_size * math.sin(angle_rad + head_angle)
        hx2 = x2 + head_size * math.cos(angle_rad - head_angle)
        hy2 = y2 + head_size * math.sin(angle_rad - head_angle)

        msp.add_line(
            (x2, y2), (hx1, hy1),
            dxfattribs={"layer": "GRAIN_DIRECTION", "color": 3}
        )
        msp.add_line(
            (x2, y2), (hx2, hy2),
            dxfattribs={"layer": "GRAIN_DIRECTION", "color": 3}
        )

    def _add_sheet_grain_indicator(
        self,
        msp,
        sheet_w: float,
        sheet_h: float,
    ) -> None:
        """Add sheet grain direction indicator in corner."""
        # Draw a small arrow in the lower-left showing sheet grain direction
        x0, y0 = 1.0, 1.0
        length = 3.0
        angle_rad = math.radians(self.sheet_grain_direction)

        x1 = x0 + length * math.cos(angle_rad)
        y1 = y0 + length * math.sin(angle_rad)

        msp.add_line(
            (x0, y0), (x1, y1),
            dxfattribs={"layer": "SHEET_GRAIN", "color": 5}  # Blue
        )

        # Label
        msp.add_text(
            "SHEET GRAIN",
            height=0.25,
            dxfattribs={"layer": "SHEET_GRAIN", "color": 5}
        ).set_pos((x0, y0 - 0.5), align="LEFT")

    def export_with_orientation(
        self,
        placements: List[Placement],
        output_dir: Path,
        engraving_depth: float = 0.02,
        laminate_cut_orders: Optional[Dict[str, List[str]]] = None,
        include_grain_arrows: bool = True,
    ) -> Tuple[Path, Path]:
        """
        Export nested DXFs with grain orientation annotations.

        Enhanced version of export() that adds:
        - Grain direction arrows on each part
        - Sheet grain indicator
        - Grain notes in the manifest

        Args:
            placements: Placed parts
            output_dir: Output directory
            engraving_depth: Depth for engraving operations
            laminate_cut_orders: Cut order by laminate type
            include_grain_arrows: Whether to draw grain arrows

        Returns:
            Tuple of (manifest_path, first_dxf_path)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows: List[str] = [
            "sheet,part,x,y,width,height,rotation,laminate,grain_note,cut_order"
        ]

        grouped: Dict[int, List[Placement]] = {}
        for placement in placements:
            grouped.setdefault(placement.sheet_index, []).append(placement)

        first_dxf = None

        for sheet_index, sheet_placements in grouped.items():
            doc = ezdxf.new()
            msp = doc.modelspace()

            # Add layers for grain annotations
            doc.layers.add("GRAIN_DIRECTION", color=3)  # Green
            doc.layers.add("SHEET_GRAIN", color=5)  # Blue

            sheet_w, sheet_h = self.stock_sheets[sheet_index]

            # Sheet outline
            msp.add_lwpolyline(
                [
                    (0, 0),
                    (sheet_w, 0),
                    (sheet_w, sheet_h),
                    (0, sheet_h),
                ],
                close=True,
                dxfattribs={"layer": "STOCK"},
            )

            # Sheet grain indicator
            if include_grain_arrows:
                self._add_sheet_grain_indicator(msp, sheet_w, sheet_h)

            for placement in sheet_placements:
                src = ezdxf.readfile(placement.outline.source)

                # Copy entities with rotation support
                if placement.rotation == 90.0:
                    self._copy_entities_rotated(
                        src, msp,
                        placement.origin[0], placement.origin[1],
                        placement.rotation
                    )
                else:
                    self._copy_entities(src, msp, *placement.origin)

                self._add_corner_relief(msp, placement, self.dogbone_radius, "DOGBONE")
                self._add_corner_relief(msp, placement, self.fillet_radius, "FILLET")
                self._add_label(msp, placement, engraving_depth)

                # Add grain direction arrow
                if include_grain_arrows:
                    self._add_grain_arrow(msp, placement)

                cut_steps = (
                    laminate_cut_orders.get(placement.outline.laminate or "")
                    if laminate_cut_orders
                    else None
                )
                cut_order = " > ".join(cut_steps or ["ENGRAVE", "PROFILE"])

                manifest_rows.append(
                    ",".join(
                        [
                            str(sheet_index),
                            placement.outline.name,
                            f"{placement.origin[0]:.3f}",
                            f"{placement.origin[1]:.3f}",
                            f"{placement.placed_width:.3f}",
                            f"{placement.placed_height:.3f}",
                            f"{placement.rotation:.0f}",
                            placement.outline.laminate or "",
                            f'"{placement.grain_note}"',
                            cut_order,
                        ]
                    )
                )

            dxf_path = output_dir / f"nested_sheet_{sheet_index}.dxf"
            doc.saveas(dxf_path)
            if first_dxf is None:
                first_dxf = dxf_path

        manifest_path = output_dir / "nest_manifest.csv"
        manifest_path.write_text("\n".join(manifest_rows))

        return manifest_path, first_dxf or output_dir / "nested_sheet_0.dxf"

    def _copy_entities_rotated(
        self,
        source_doc: ezdxf.document.Drawing,
        target_msp,
        dx: float,
        dy: float,
        rotation: float,
    ) -> None:
        """Copy entities with rotation applied."""
        for entity in source_doc.modelspace():
            copied = entity.copy()
            # Rotate about origin, then translate
            if hasattr(copied, 'transform'):
                import ezdxf.math as emath
                # Create rotation matrix
                angle_rad = math.radians(rotation)
                copied.rotate(angle_rad)
            copied.translate(dx, dy, 0)
            target_msp.add_entity(copied)


__all__ = ["Outline", "Placement", "NestingPlanner", "GrainConstraint"]
