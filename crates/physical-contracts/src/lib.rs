//! Types shared by every part of Physical.
//!
//! This crate depends on nothing else in the workspace and nothing outside it
//! beyond serialization. A third party implementing the module contract needs
//! only this crate and the specification in `spec/`.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod capability;
pub mod device;
pub mod manifest;

pub use capability::{Capability, Permission, UsbClass};
pub use device::{BayId, DeviceDescriptor, HotplugEvent};
pub use manifest::{Binding, ModuleManifest};

/// The module contract version this build implements.
pub const CONTRACT_VERSION: &str = "0.1";
