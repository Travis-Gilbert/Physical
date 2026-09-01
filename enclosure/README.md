# enclosure/

The shell is a function of the installed module set, so it is written as code
rather than drawn in a GUI. Regenerating the case for a different bay
configuration is a build step, not an afternoon.

## Run

    pip install build123d
    python enclosure.py          # writes build/physical-core.{step,stl}
    python block.py              # writes build/block-{1x1,2x1,3x1}.{step,stl}

Preview renders (no GPU, no GUI):

    pip install trimesh matplotlib
    # see preview.py

## Reference dimensions

Verified, not assumed:

- **Framework Expansion Card — 38 × 7 × 30 mm** (depth × height × width), per
  Framework's published product specs. The bay opening is this plus `FIT`.
- **CFexpress Type B — 38.5 × 29.8 × 3.8 mm.** Nearly the same face as a
  Framework card, just thinner, which is why a cartridge carrier is simply a
  Framework shell with a CFexpress socket inside it.

## What drives the geometry

`Config` is the whole interface. Outer width is *derived* from `bay_count` and
`bay_pitch` — it is never a magic number:

    bay_bank_width = (bay_count - 1) * bay_pitch + 30
    width          = bay_bank_width + port_cluster + 2*wall + 12

Verified variants:

| config | bays | outer | 6061 mass |
|---|---|---|---|
| `physical-mini` | 2 | 140 × 110 × 45 | 271 g |
| `physical-core` | 6 | 276 × 150 × 45 | 587 g |
| `physical-wide` | 10 | 412 × 170 × 45 | 912 g |

## Design notes

- **34 mm bay pitch.** The card is 30 wide, leaving 4 mm of web between
  openings. Six penetrations through one face costs rigidity; the web and the
  internal guide rail are what buy it back. Cards register against the rail,
  not against the shell.
- **3 mm wall.** Also the heatsink mass, so it is not minimised for its own
  sake. Fanless.
- **Floor vents** sit under the carrier board. The NVMe is the hot spot under
  sustained write, not the SoC.
- **Cartridge bezel** is a 1.5 mm recess in the outer face, with the card
  opening passing through the remaining wall. It reads as the hero feature
  rather than as a seventh port.

## block.py

The visible tier. Blocks are screens, knobs, speakers, lights, sensors — things
you look at or touch — and they sit on the core and on each other.

Grid is **34 mm, the same pitch as the rear bay bank**, so a block lands
directly above the bay it relates to and one number drives the whole family.
1×1 is 33.5 mm square (34 minus a 0.5 mm gap so neighbours do not fight),
22 mm tall.

Mating stack, bottom to top:

| surface | carries |
|---|---|
| core lid | flat gold pads, recessed |
| block underside | spring pins, magnets, alignment sockets |
| block topside | flat gold pads, alignment bosses |

Spring pins always point **down**, carried by the block, so nothing springy is
ever exposed and an unstacked block has a clean flat top.

Contacts, 8 at 2.54 mm: `VHI GND D+ D- GND SDA SCL PRESENT`. USB 2.0 plus an
I2C sideband. USB 3 stays on the bays with a real connector — 5 Gbps over
spring contacts is an RF problem and this is not the place to solve it.

The sideband is not decoration. USB enumeration says a device exists, not
*where it physically is*; the addressed I2C line is what lets
`DeviceDescriptor.bay` hold something real, so an operator can be told "the
block in position 2" rather than a sysfs path.

Alignment bosses sit on **one diagonal only**. Two features on a diagonal fix
position and rotation at once, and the asymmetry keys orientation
mechanically — a block turned 90 degrees will not seat.

Magnet pockets are blind from the interior with `magnet_skin` left over them,
so no magnet is visible from outside.

Power follows the same pattern as other modular systems that work: high
voltage in on `VHI`, regulated locally inside each block. Distributing 5 V
instead browns out partway along a chain.

## Verification

Correctness is checked geometrically rather than by eye. Worth re-running after
any change:

- mesh is watertight
- rear wall cross-section has `1 + bay_count + 3` loops (outer boundary, bays,
  and the GbE / USB-C / HDMI cluster)

Two modelling bugs were caught this way that would not have been caught
visually: the port cluster overhanging the shell edge, and the cartridge bezel
cutting through the wall instead of recessing into it.

## preview.py

A small orthographic z-buffer rasterizer. matplotlib's `Poly3DCollection` has
no depth buffer, so a solid with holes renders inside-out. This does backface
culling, barycentric fill, lambert shading, and depth cueing.

Two bugs found here, both of which produced plausible-looking wrong pictures:

- **No depth cue.** An interior surface seen through a bay opening shaded
  identically to the near wall, so a correctly-cut six-bay bank rendered as a
  solid slab and sent me hunting a modelling bug that did not exist.
- **Inverted depth and cull.** `w = -(verts @ fwd)` with the cull on
  `normals @ (-fwd)` rendered the *antipodal* viewpoint. Both were negated, so
  the images were internally consistent and looked plausible — but a requested
  plan view returned the underside, and blocks placed on top of the core were
  hidden behind it. `fwd` points from the origin toward the camera, so a
  vertex's projection onto it is its nearness; no negation belongs there.

Sanity check that catches the second one:

    from preview import _basis
    _, _, fwd = _basis(90, -90)          # plan view
    keep = (mesh.face_normals @ fwd) > 0
    mesh.face_normals[keep][:, 2].mean() # must be positive

## Known gaps

- The lid is a separate part and does not exist yet, so blocks currently seat
  on the open rim in assembly renders.
- The core has no contact pad array yet; blocks mate to a lid still to be
  designed.
- No fastener bosses.
- The SoM standoff pattern is a placeholder 70 × 45 rectangle until a module is
  chosen and its real hole pattern is used.
- Nothing is thermally simulated. 3 mm of aluminium for ~10 W is a reasonable
  first guess, not a verified one.
- USB 2.0 over spring contacts is assumed workable and is not yet validated on
  hardware.
