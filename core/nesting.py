"""Nesting and CAM prep utilities.

Provides a lightweight bin-packing optimizer that ingests DXF outlines,
places them on available stock sheets, and emits nested DXFs plus a CSV
manifest suitable for CAM import. Post-processing adds dogbones/fillets
and label engraving layers to preserve cut ordering.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import ezdxf
from ezdxf import bbox


@dataclass
class Outline:
    """Single part outline sourced from a DXF."""

    name: str
    source: Path
    width: float
    height: float
    quantity: int = 1
    laminate: Optional[str] = None


@dataclass
class Placement:
    """Placement of an outline on a specific sheet."""

    outline: Outline
    sheet_index: int
    origin: Tuple[float, float]
    rotation: float = 0.0

    @property
    def label_position(self) -> Tuple[float, float]:
        x0, y0 = self.origin
        return x0 + self.outline.width / 2, y0 + self.outline.height / 2


class NestingPlanner:
    """Performs simple shelf-based nesting for DXF outlines."""

    def __init__(
        self,
        stock_sheets: List[Tuple[float, float]],
        margin: float = 0.25,
        spacing: float = 0.125,
        dogbone_radius: float = 0.0,
        fillet_radius: float = 0.0,
    ):
        self.stock_sheets = stock_sheets
        self.margin = margin
        self.spacing = spacing
        self.dogbone_radius = dogbone_radius
        self.fillet_radius = fillet_radius

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

    def pack(self, outlines: Iterable[Outline]) -> List[Placement]:
        """Greedy shelf packer across the configured stock sheets."""

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
                # Move to next row if needed
                if cursor_x + outline.width + self.margin > sheet_w:
                    cursor_x = self.margin
                    cursor_y += row_height + self.spacing
                    row_height = 0.0

                # Move to next sheet if vertical space is exhausted
                if cursor_y + outline.height + self.margin > sheet_h:
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
                    )
                )
                cursor_x += outline.width + self.spacing
                row_height = max(row_height, outline.height)

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
                    laminate_cut_orders.get(placement.outline.laminate)
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


__all__ = ["Outline", "Placement", "NestingPlanner"]
