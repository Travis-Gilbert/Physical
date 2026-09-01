"""Parametric snap-on block.

Blocks are the *visible* tier of the module system: screens, knobs, speakers,
lights, sensors. Things you look at or touch. They sit on top of the core, and
on each other.

The fast tier is separate. Storage, capture, and network live in rear bays on
real USB-C connectors, because 5 Gbps over spring contacts is an RF problem and
this is not the place to solve it. Blocks run USB 2.0 plus an I2C sideband,
which is plenty for a display or a control surface.

Why the sideband exists: USB enumeration tells the daemon that a device is
present, not *where it physically is*. The addressed I2C line is what lets
`DeviceDescriptor.bay` be populated with something real, so an operator can be
told "the block in position 2" instead of a sysfs path.

Grid: one unit is 34 mm, the same pitch as the rear bay bank. A block therefore
lands directly above the bay it relates to, and one number drives the whole
product family.

Mating stack, bottom to top:

    core lid          flat gold pads, recessed
    block underside   spring pins + magnets + alignment sockets
    block topside     flat gold pads + alignment bosses

Spring pins always point *down*, carried by the block. Nothing springy is ever
exposed on a top surface, so an unstacked block has a flat clean face.

Usage:
    python block.py          # writes STEP + STL for 1x1, 2x1, 3x1
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Part,
    Pos,
    export_step,
    export_stl,
    fillet,
)

#: Grid pitch. Identical to `enclosure.Config.bay_pitch` on purpose.
GRID = 34.0

#: Contact order, left to right, viewed from the block underside.
#: VHI is the high-voltage rail; each block regulates locally, so a chain of
#: blocks does not brown out the way a distributed 5 V rail would.
CONTACTS = ("VHI", "GND", "D+", "D-", "GND", "SDA", "SCL", "PRESENT")


@dataclass
class BlockConfig:
    """One block."""

    units_x: int = 1
    units_y: int = 1
    height: float = 22.0

    wall: float = 2.0
    corner_radius: float = 3.0
    gap: float = 0.5
    """Shrink per grid unit, so neighbours do not fight for the same space."""

    # Contacts --------------------------------------------------------
    pin_pitch: float = 2.54
    pin_hole_d: float = 1.5
    pad_d: float = 3.0
    pad_recess: float = 0.6

    # Magnets ---------------------------------------------------------
    magnet_d: float = 6.0
    magnet_h: float = 3.0
    magnet_skin: float = 0.6
    """Material left over a magnet pocket. Pockets are blind from the inside,
    so no magnet is visible from outside."""
    magnet_inset: float = 7.0

    # Alignment -------------------------------------------------------
    boss_d: float = 4.0
    boss_h: float = 1.6
    boss_offset: float = 11.0
    """Bosses sit on one diagonal only. Two features on a diagonal fix both
    position and rotation, and the asymmetry keys orientation mechanically —
    a block turned 90 degrees will not seat."""

    name: str = "block-1x1"

    @property
    def width(self) -> float:
        return self.units_x * GRID - self.gap

    @property
    def depth(self) -> float:
        return self.units_y * GRID - self.gap

    @property
    def contact_span(self) -> float:
        return (len(CONTACTS) - 1) * self.pin_pitch


def _contact_positions(cfg: BlockConfig) -> list[float]:
    """X offsets of each contact, centred on the block."""
    start = -cfg.contact_span / 2
    return [start + i * cfg.pin_pitch for i in range(len(CONTACTS))]


def _magnet_positions(cfg: BlockConfig) -> list[tuple[float, float]]:
    """Magnet centres, inset from each corner."""
    x = cfg.width / 2 - cfg.magnet_inset
    y = cfg.depth / 2 - cfg.magnet_inset
    return [(sx * x, sy * y) for sx in (-1, 1) for sy in (-1, 1)]


def _boss_positions(cfg: BlockConfig) -> list[tuple[float, float]]:
    """Alignment features, on one diagonal only."""
    x = cfg.width / 2 - cfg.boss_offset
    y = cfg.depth / 2 - cfg.boss_offset
    return [(-x, -y), (x, y)]


def build_block(cfg: BlockConfig) -> Part:
    """Generate one block."""
    w, d, h = cfg.width, cfg.depth, cfg.height

    body = Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = fillet(body.edges().filter_by(Axis.Z), radius=cfg.corner_radius)

    # Interior. Open at the bottom; the PCB drops in and a base plate closes it.
    cavity = Pos(0, 0, cfg.wall) * Box(
        w - 2 * cfg.wall,
        d - 2 * cfg.wall,
        h - 2 * cfg.wall,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - cavity

    # --- Underside: spring pin through-holes -------------------------
    for x in _contact_positions(cfg):
        hole = Cylinder(
            radius=cfg.pin_hole_d / 2,
            height=cfg.wall * 3,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body - (Pos(x, 0, -cfg.wall) * hole)

    # --- Topside: pad recesses ---------------------------------------
    # Flat gold pads for the next block's pins to land on. Recessed so the
    # top face stays flush and wipes clean.
    for x in _contact_positions(cfg):
        pad = Cylinder(
            radius=cfg.pad_d / 2,
            height=cfg.pad_recess * 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body - (Pos(x, 0, h - cfg.pad_recess) * pad)

    # --- Magnet pockets ----------------------------------------------
    # Blind from the interior in both directions, leaving `magnet_skin` of
    # material so nothing is visible from outside.
    for mx, my in _magnet_positions(cfg):
        lower = Cylinder(
            radius=cfg.magnet_d / 2,
            height=cfg.magnet_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body - (Pos(mx, my, cfg.magnet_skin) * lower)

        upper = Cylinder(
            radius=cfg.magnet_d / 2,
            height=cfg.magnet_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body - (
            Pos(mx, my, h - cfg.magnet_skin - cfg.magnet_h) * upper
        )

    # --- Alignment: boss up, socket down -----------------------------
    for bx, by in _boss_positions(cfg):
        boss = Cylinder(
            radius=cfg.boss_d / 2,
            height=cfg.boss_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body + (Pos(bx, by, h) * boss)

        socket = Cylinder(
            radius=(cfg.boss_d + 0.3) / 2,
            height=cfg.boss_h + 0.3,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        body = body - (Pos(bx, by, -0.01) * socket)

    return body


def main() -> None:
    out = Path(__file__).parent / "build"
    out.mkdir(exist_ok=True)

    variants = [
        BlockConfig(units_x=1, units_y=1, name="block-1x1"),
        BlockConfig(units_x=2, units_y=1, name="block-2x1"),
        BlockConfig(units_x=3, units_y=1, name="block-3x1"),
    ]

    print(f"grid {GRID:.0f} mm   contacts: {' '.join(CONTACTS)}")
    for cfg in variants:
        part = build_block(cfg)
        export_step(part, str(out / f"{cfg.name}.step"))
        export_stl(part, str(out / f"{cfg.name}.stl"))
        print(
            f"  {cfg.name:12s} {cfg.width:6.1f} x {cfg.depth:5.1f} x "
            f"{cfg.height:4.1f} mm"
        )


if __name__ == "__main__":
    main()
