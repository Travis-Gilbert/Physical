# ui

The client surface for a Physical host. Physical is headless; this is a
*client*, and the core does not depend on it.

## Contract, not framework

A UI reaches the core over its HTTP/WS API and nothing else. There is no shared
crate, no imported component library, no renderer assumption baked into the
daemon. Swap the client and the core does not notice.

## Intended renderer

Agentic GPUI (AGPUI), which runs both as a native window and in the browser via
WebGPU/WASM — so one client covers the desktop app and the phone/TV browser
without a second implementation.

AGPUI is still in development (Theorem PR #646 is not yet mergeable), so this
directory is a seam, not an implementation. Building the core against the
*protocol* rather than against AGPUI crates is deliberate: the core ships on its
own timeline, and a third party can put an entirely different face on it.

Not Leptos. That path is being retired in Theorem and is not used here.

## Status

Empty by design. The API it will target is specified in `spec/`.
