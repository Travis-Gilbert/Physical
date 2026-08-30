# enclosure/

The shell is a function of the installed module set, so it is written as code
rather than drawn in a GUI. Regenerating the case for a different bay
configuration is a build step, not an afternoon.

## Run

    pip install build123d
    python enclosure.py          # writes build/physical-core.{step,stl}

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

## Verification

`enclosure.py` exports; correctness is checked geometrically rather than by
eye. Both are worth re-running after any change:

- mesh is watertight
- rear wall cross-section has `1 + bay_count + 3` loops (outer boundary, bays,
  and the GbE / USB-C / HDMI cluster)

Two bugs were caught this way and would not have been caught visually: the
port cluster overhanging the shell edge, and the cartridge bezel cutting
through the wall instead of recessing into it.

## preview.py

A small orthographic z-buffer rasterizer. matplotlib's `Poly3DCollection` has
no depth buffer, so a solid with holes renders inside-out. This does backface
culling, barycentric fill, lambert shading, and depth cueing — the last one
matters, because without it an interior surface seen through a bay opening
shades identically to the near wall and a correctly-cut bay bank looks like
solid metal.

## Known gaps

- The lid is a separate part and does not exist yet.
- No fastener bosses.
- The SoM standoff pattern is a placeholder 70 × 45 rectangle until a module is
  chosen and its real hole pattern is used.
- Nothing is thermally simulated. 3 mm of aluminium for ~10 W is a reasonable
  first guess, not a verified one.
