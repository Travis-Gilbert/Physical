# SPEC-MODULE-CONTRACT-0.1

The interface between a Physical host and a module.

Status: draft. Nothing implements this yet.

## Goals

- A module binds to hardware by **class**, never by identity, so a module
  written today accepts hardware released years from now.
- A host can decide what a module may reach by reading its manifest, without
  reading its code.
- A third party can implement this contract using only `physical-contracts` and
  this document.

## Desired end state

An operator plugs in a device the host has never seen. The kernel enumerates it,
the host resolves a capability from the claimed class, and any installed module
declaring that capability is offered the binding. If nothing claims it, the
device is still visible, still described, and the operator is told why nothing
picked it up.

## Capability vocabulary

A capability is what a module binds to. The set is closed; adding one is a
contract version bump.

| Capability | Source |
|---|---|
| `usb:mass-storage` | USB base class `0x08` |
| `usb:video` | USB base class `0x0e` |
| `usb:audio` | USB base class `0x01` |
| `usb:printer` | USB base class `0x07` |
| `usb:still-image` | USB base class `0x06` |
| `usb:hid` | USB base class `0x03` |
| `usb:communications` | USB base class `0x02` |
| `usb-vendor:VVVV:PPPP` | Vendor-specific (`0xff`) or unrecognised class |
| `optical:audio-disc` | Optical drive with a Red Book disc present |
| `vault:volume` | Block device admitted as vault storage |
| `vault:cartridge` | Cartridge in the front slot |
| `net:ipp-printer` | IPP printer discovered over mDNS |
| `service:NAME` | A service another module provides |

### Vendor binding is deliberately awkward

`usb-vendor:` exists so hardware with no standard class is reachable, not as a
convenience. It requires naming a vendor ID, it is the only path for
`VendorSpecific` and unrecognised classes, and hosts should surface it
differently in the UI. Class binding stays the default because class binding is
what makes unknown hardware work.

## Manifest

```json
{
  "id": "dev.example.cd-vault",
  "name": "CD Vault",
  "version": "0.1.0",
  "description": "Rips audio CDs into the catalog and burns discs from it.",
  "contract": "0.1",
  "consumes": [
    { "kind": "optical-audio-disc" },
    { "kind": "usb", "class": "mass-storage" }
  ],
  "provides": [
    { "kind": "service", "0": "cd.rip" }
  ],
  "permissions": [
    { "kind": "graph-write", "label": "Album" },
    { "kind": "vault-write" }
  ],
  "source": "https://github.com/example/cd-vault",
  "license": "Apache-2.0"
}
```

`source` is required. A module with no published source is not installable from
the first-party registry.

## Permissions

Additive and explicit. A module with no grants can compute and respond, and
nothing else. The host shows the full grant list before install.

| Permission | Grants |
|---|---|
| `graph-read{label}` | Read catalog nodes carrying that label |
| `graph-write{label}` | Create and update nodes under a label it owns |
| `vault-read` | Read bytes from vault storage |
| `vault-write` | Write bytes to vault storage |
| `network-egress` | Reach beyond the local subnet |
| `agent-invoke` | Call the configured agent endpoint |

## Binding

1. Kernel enumerates. udev emits.
2. Host builds a `DeviceDescriptor` including bound driver and negotiated link
   speed.
3. Host resolves a `Capability` from the claimed class. Vendor-specific and
   unrecognised classes resolve to `usb-vendor:` and are not offered
   generically.
4. Every installed module whose `consumes` accepts that capability is offered
   the binding.
5. On conflict the operator chooses. The host does not guess, and it records the
   choice.
6. The resulting `Binding` records **which capability matched**, so the answer to
   "why did that module claim my device" is stored rather than reconstructed.

## Diagnostics

The descriptor carries `driver` and `speed_mbps` because they answer the two
most common failures:

- `driver: null` — nothing bound. Usually a vendor-specific device with no
  module installed.
- `speed_mbps: 480` on a device expected at 5000 — bad cable, or a USB 2 port.

An agent can only ask about fields it knows exist, which is why these are part
of the descriptor rather than an on-demand lookup.

## Non-goals

- No device database. No VID/PID table ships with the host.
- No playback. Modules may decode for indexing; clients play.
- No module in the default image that circumvents an access control.
- No capability added without a contract version bump.

## Open questions

- Does `provides` need versioning independent of the module version?
- How does a module declare that it needs *exclusive* access to a device?
- Should `service:` resolution be late-bound or resolved at install?
