# Physical

An extensible hardware core for a personal media and life vault.

Physical is a headless appliance: it stores things you own, indexes them, serves
them to devices you already have, and runs an agent you point at whatever model
you want. It plays nothing back itself. It renders nothing itself. It is a
server, a catalog, and a set of ports.

Everything beyond the core is a module.

## Why this shape

The core is deliberately boring. A neutral staple with a stable extension
contract outlives any specific feature set, and lets people build things neither
the author nor the buyer imagined. Postgres is the model: a small core, a
documented extension API, and a registry that does not vet.

## Architecture

```
                    ┌─────────────────────────────┐
   phone / TV ──────┤  physical-core (headless)   │
   browser   HTTP/WS│                             │
                    │  RustyRed graph  (catalog)  │
                    │  module registry            │
                    │  agent binding (bring your  │
                    │    own model endpoint)      │
                    └──────┬───────────────┬──────┘
                           │               │
                    physical-hotplug   NVMe vault
                    (udev → events)    + cartridge
                           │
              ┌────────────┴────────────┐
              │  expansion bays (USB-C) │
              └─────────────────────────┘
```

### The bay is a USB-C port

Modules dock into bays that follow Framework Computer's Expansion Card
mechanical envelope (38 x 30 x 7 mm), published under CC BY 4.0. Framework
Expansion Cards are standard USB-C adapters, which means:

- existing Framework cards (storage, USB-A, HDMI, DisplayPort, microSD, 2.5GbE)
  work in a Physical host on day one;
- a Physical module also works in a Framework laptop, a DockFrame hub, or a
  phone with reverse charging;
- no new mechanical standard has to be invented, documented, or defended.

Reference: https://github.com/FrameworkComputer/ExpansionCards

### Devices bind by capability, not by identity

Physical never ships a device database. USB defines standard device classes and
Linux already implements them. A module declares the capabilities it *consumes*
(`usb:video`, `usb:printer`, `usb:mass-storage`), and unknown hardware routes
itself by class the moment it enumerates.

This is why a $3 UVC capture chip and a 2019 printer both work with nothing
installed, and why a module written today can bind to hardware released in five
years.

## Repository layout

| Path | Contents |
|---|---|
| `crates/physical-contracts` | Capability vocabulary, device descriptors, module manifests. No dependencies on anything else in the workspace. |
| `crates/physical-hotplug` | udev bridge. Turns kernel hotplug into typed capability events. |
| `crates/physical-core` | The daemon: graph binding, module registry, HTTP/WS API. |
| `crates/physical-cli` | Operator tooling. |
| `spec/` | The module contract. Versioned, independently implementable. |
| `enclosure/` | Parametric enclosure as code (build123d). The shell is a function of the installed module set. |
| `hardware/cards/` | KiCad designs for first-party expansion cards. |
| `tokens/` | Neutral DTCG design tokens. Themes are extensions. |
| `ui/` | Decision record only. The client surface is AGPUI once it lands; see `ui/README.md`. |

## Dependency rule

Physical depends on **protocol**, never on another repository's crates. The core
speaks HTTP/WS; every client, including the first-party one, is a consumer of
that wire contract rather than a compilation unit linked against it.

This matters more, not less, now that the intended client is AGPUI. The UI can
land whenever it is ready without Physical's schedule being tied to it, and a
third party can build an entirely different client against the same API.

## What ships in the core

Storage. Indexing. Serving. Hotplug routing. Module registry. Agent binding.
Audio CD rip and burn (Red Book CD-DA carries no access control).

## What does not ship in the core

Anything that circumvents an access control. That includes CSS and AACS
decryption. Those may exist as third-party modules; they are not distributed
here, are not in the default image, and are not described in this project's
documentation as a reason to buy anything.

## Non-goals

- No local model inference in v1. Point the agent at your own endpoint.
- No playback. Clients play; the box serves.
- No features behind flags.
- No crates that nothing calls.

## Status

Scaffold. Nothing is implemented.

## License

Apache-2.0
