"""Parametric enclosure for a Physical host.

The shell is a function of the installed module set, so it is generated rather
than drawn. Change `Config`, re-run, get a new case.

Reference dimensions, verified rather than assumed:

- Framework Expansion Card: 38 x 7 x 30 mm (depth x height x width), per
  Framework's published product specifications.
- CFexpress Type B: 38.5 x 29.8 x 3.8 mm. Note this is nearly the same face as
  a Framework card, which is why a cartridge carrier is simply a Framework
  shell with a CFexpress socket inside it.

Coordinates: X is width (left-right), Y is depth (front is -Y, rear is +Y),
Z is height (bottom at Z=0).

Usage:
    python enclosure.py            # writes STEP + STL for the default config
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

# --- Fixed external standards. Not tunable; these are somebody else's spec. ---

CARD_DEPTH = 38.0
CARD_HEIGHT = 7.0
CARD_WIDTH = 30.0

CFEXPRESS_B = (38.5, 29.8, 3.8)

#: Clearance applied to every opening a user-inserted part passes through.
FIT = 0.4


@dataclass
class Config:
    """Everything that varies between builds of the case."""

    # Module complement -------------------------------------------------
    bay_count: int = 6
    """Rear-facing expansion bays."""

    cartridge_bay: bool = True
    """Front-facing bay with a wider bezel, for the cartridge."""

    has_capture: bool = True
    """Fit the internal MS2130; adds a rear HDMI-in cutout."""

    has_nvme: bool = True
    """Internal M.2 vault; adds standoffs and a thermal pad boss."""

    # Bay bank ----------------------------------------------------------
    bay_pitch: float = 34.0
    """Centre-to-centre bay spacing. Card is 30 wide, so this leaves 4mm of
    web between openings, which is what keeps the rear face stiff."""

    bay_z: float = 12.0
    """Height of bay centreline above the inside floor."""

    # Shell -------------------------------------------------------------
    wall: float = 3.0
    """Aluminium wall thickness. Also the heatsink mass, so it is not
    minimised for its own sake."""

    corner_radius: float = 6.0
    floor_margin: float = 14.0
    """Free depth behind the bay bank for the carrier board and hubs."""

    height: float = 45.0
    depth: float = 150.0

    # Internals ---------------------------------------------------------
    som_size: tuple[float, float] = (70.0, 45.0)
    som_standoff_inset: float = 4.0
    som_standoff_h: float = 6.0
    som_standoff_d: float = 5.0

    vent_slots: int = 14
    vent_slot_w: float = 3.0
    vent_slot_l: float = 60.0

    # Fixed rear ports --------------------------------------------------
    gbe: tuple[float, float] = (16.0, 13.5)
    usbc_pd: tuple[float, float] = (9.2, 3.4)
    hdmi_in: tuple[float, float] = (15.2, 5.6)

    name: str = "physical-core"

    # Derived -----------------------------------------------------------
    @property
    def bay_bank_width(self) -> float:
        """Width consumed by the rear bay bank, edge to edge."""
        if self.bay_count <= 0:
            return 0.0
        return (self.bay_count - 1) * self.bay_pitch + CARD_WIDTH

    @property
    def width(self) -> float:
        """Outer width. Driven by the bay bank, never guessed."""
        # Bank, plus room for the fixed port cluster, plus both walls.
        port_cluster = 58.0
        return self.bay_bank_width + port_cluster + 2 * self.wall + 12.0

    @property
    def inner(self) -> tuple[float, float, float]:
        return (
            self.width - 2 * self.wall,
            self.depth - 2 * self.wall,
            self.height - self.wall,
        )


def _slot(w: float, h: float, depth: float, max_r: float | None = None) -> Part:
    """A rounded rectangular cutter, axis along Y.

    `max_r` caps the corner radius. Without it a near-square opening such as
    an RJ45 fillets into a circle, because the default radius is half the
    shorter side.
    """
    cutter = Box(w, depth, h)
    r = min(w, h) / 2 - 0.01
    if max_r is not None:
        r = min(r, max_r)
    if r > 0.2:
        cutter = fillet(cutter.edges().filter_by(Axis.Y), radius=r)
    return cutter


def build(cfg: Config) -> Part:
    """Generate the enclosure solid for `cfg`."""
    w, d, h = cfg.width, cfg.depth, cfg.height
    iw, idp, ih = cfg.inner

    # Outer shell, bottom face on Z=0.
    shell = Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shell = fillet(shell.edges().filter_by(Axis.Z), radius=cfg.corner_radius)

    # Hollow it. Open at the top: the lid is a separate part.
    cavity = Pos(0, 0, cfg.wall) * Box(
        iw, idp, ih, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    shell = shell - cavity

    # --- Rear bay bank -------------------------------------------------
    z = cfg.wall + cfg.bay_z
    bank_left = -cfg.bay_bank_width / 2 + CARD_WIDTH / 2
    rear_y = d / 2

    for i in range(cfg.bay_count):
        x = bank_left + i * cfg.bay_pitch
        opening = _slot(CARD_WIDTH + FIT, CARD_HEIGHT + FIT, cfg.wall * 4)
        shell = shell - (Pos(x, rear_y, z) * opening)

    # --- Fixed rear ports, right of the bank ---------------------------
    # Centre the cluster in the flat region between the bank and the corner
    # radius, rather than at a guessed offset. The previous hard-coded 26mm
    # ran the GbE opening off the edge of the shell.
    bank_edge = cfg.bay_bank_width / 2
    flat_edge = w / 2 - cfg.corner_radius
    port_x = (bank_edge + flat_edge) / 2

    shell = shell - (
        Pos(port_x, rear_y, z) * _slot(*cfg.gbe, cfg.wall * 4, max_r=1.5)
    )
    shell = shell - (
        Pos(port_x, rear_y, z + 20.0) * _slot(*cfg.usbc_pd, cfg.wall * 4)
    )
    if cfg.has_capture:
        shell = shell - (
            Pos(port_x - 22.0, rear_y, z + 20.0)
            * _slot(*cfg.hdmi_in, cfg.wall * 4)
        )

    # --- Front cartridge bay -------------------------------------------
    # Same envelope as any other bay; the bezel is wider so it reads as the
    # hero feature rather than as a seventh port.
    if cfg.cartridge_bay:
        front_y = -d / 2
        bezel_w, bezel_h = CARD_WIDTH + 10.0, CARD_HEIGHT + 6.0
        bezel_depth = 1.5
        # Recess: cut only `bezel_depth` into the outer face. Sized and
        # positioned so the cutter's inner limit stops short of the wall's
        # inner surface, leaving material for the card opening to pass through.
        bezel = _slot(bezel_w, bezel_h, bezel_depth * 2)
        shell = shell - (Pos(0, front_y - bezel_depth, z) * bezel)
        # Card opening: all the way through.
        shell = shell - (
            Pos(0, front_y, z) * _slot(CARD_WIDTH + FIT, CARD_HEIGHT + FIT, cfg.wall * 6)
        )

    # --- Floor vents ---------------------------------------------------
    # Convection path under the carrier board. The NVMe is the hot spot under
    # sustained write, not the SoC.
    if cfg.vent_slots:
        pitch = (iw - 30.0) / max(cfg.vent_slots - 1, 1)
        start = -(iw - 30.0) / 2
        for i in range(cfg.vent_slots):
            x = start + i * pitch
            vent = Box(cfg.vent_slot_w, cfg.vent_slot_l, cfg.wall * 3)
            vent = fillet(
                vent.edges().filter_by(Axis.Z), radius=cfg.vent_slot_w / 2 - 0.01
            )
            shell = shell - (Pos(x, -12.0, 0) * vent)

    # --- SoM standoffs -------------------------------------------------
    sx, sy = cfg.som_size
    inset = cfg.som_standoff_inset
    som_centre_y = d / 2 - cfg.wall - CARD_DEPTH - cfg.floor_margin - sy / 2
    for dx in (-1, 1):
        for dy in (-1, 1):
            post = Cylinder(
                radius=cfg.som_standoff_d / 2,
                height=cfg.som_standoff_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            shell = shell + (
                Pos(
                    dx * (sx / 2 - inset),
                    som_centre_y + dy * (sy / 2 - inset),
                    cfg.wall,
                )
                * post
            )

    # --- Card guide rails ----------------------------------------------
    # Cards register against an internal rail, not against the shell. Six
    # penetrations through one face costs rigidity; this is what buys it back.
    if cfg.bay_count:
        rail = Box(cfg.bay_bank_width + 8.0, 3.0, 4.0)
        shell = shell + (
            Pos(0, d / 2 - cfg.wall - CARD_DEPTH, cfg.wall) * rail
        )

    return shell


def main() -> None:
    cfg = Config()
    out = Path(__file__).parent / "build"
    out.mkdir(exist_ok=True)

    part = build(cfg)

    print(f"{cfg.name}: {cfg.width:.1f} x {cfg.depth:.1f} x {cfg.height:.1f} mm")
    print(f"  bays: {cfg.bay_count} (bank {cfg.bay_bank_width:.1f} mm)")
    print(f"  cartridge: {cfg.cartridge_bay}  capture: {cfg.has_capture}")

    export_step(part, str(out / f"{cfg.name}.step"))
    export_stl(part, str(out / f"{cfg.name}.stl"))
    print(f"  wrote {out}/{cfg.name}.step and .stl")


if __name__ == "__main__":
    main()
