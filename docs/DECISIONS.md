# Decisions

Short records. Reversible ones say so.

## D1 — The bay is a USB-C port

Adopt Framework Computer's Expansion Card mechanical envelope (CC BY 4.0)
instead of inventing one. Framework cards are standard USB-C adapters, so the
electrical contract is USB and the mechanical contract is already published,
tested, and has third-party designers using it.

Consequence: existing Framework cards work here on day one, and Physical cards
work in Framework laptops and USB-C phones.

## D2 — Bind by class, never by identity

No VID/PID database ships. Modules declare USB classes they consume. Vendor
binding exists but is deliberately more awkward.

Consequence: hardware released after a module is written still works.

## D3 — Protocol boundary, no cargo edge into Theorem

`physical-core` exposes HTTP/WS. No crate in this workspace links against
another repository's crates.

Consequence: Physical ships on its own schedule; a third party can build a
different client against the same API.

## D4 — No UI framework scaffolded yet

AGPUI is the intended client and targets browser (WebGPU/WebGL2) and native from
one renderer. It is not mergeable yet. `ui/` stays empty rather than acquiring a
placeholder that would later have to be deleted.

Reversible: if AGPUI stalls, revisit. The protocol boundary in D3 is what makes
it cheap to revisit.

## D5 — Neutral tokens, themes as extensions

The base palette is characterless on purpose. Products built on this core should
not all look like the same product.

## D6 — The core ships clean

No module that circumvents an access control is in the default image, in this
repository, or described in its documentation. Audio CD handling is in the core
because Red Book CD-DA carries no access control.
