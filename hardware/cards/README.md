# hardware/cards/

First-party expansion cards.

A card is a **standard USB-C device** in Framework's mechanical envelope. That
is the entire electrical contract. A card built here also works in a Framework
laptop or a USB-C phone with reverse charging, and a Framework card works in a
Physical host.

Framework publishes a KiCad template with part numbers and an example card built
around an STM32. Start from it rather than from a blank schematic.

## Candidates

| Card | Silicon | Notes |
|---|---|---|
| HDMI capture | MacroSilicon MS2130 | UVC-compliant, ~$3 at LCSC, needs no driver |
| Cartridge reader | CFexpress Type B socket | PCIe NVMe behind a bridge |
| Optical | off-the-shelf USB drive, re-housed | Audio CD only in the default image |

## Tooling

KiCad 10 for anything intended to be manufactured — free, no commercial
restriction. EasyEDA is an option for quick JLCPCB/LCSC turnaround since the
parts are priced there already. Note EAGLE is dead as of June 2026.
