//! The udev bridge.
//!
//! This is the seam where kernel hotplug becomes something the rest of Physical
//! can reason about. It does two things and nothing else: enumerate what is
//! attached now, and stream changes as they happen. Deciding what a device
//! *means* belongs to the core's registry, not here.
//!
//! Linux only. There is no portable hotplug abstraction worth the indirection;
//! the appliance is a Linux appliance.

#![forbid(unsafe_code)]
#![warn(missing_docs)]

use physical_contracts::{DeviceDescriptor, HotplugEvent};

/// Why a hotplug operation failed.
#[derive(Debug, thiserror::Error)]
pub enum HotplugError {
    /// The udev context could not be opened.
    #[error("could not open udev context: {0}")]
    Context(#[source] std::io::Error),
    /// The monitor could not be established.
    #[error("could not start udev monitor: {0}")]
    Monitor(#[source] std::io::Error),
}

/// A source of hotplug events.
pub trait HotplugSource {
    /// Everything attached right now.
    ///
    /// Called once at startup so the core does not begin with an empty world
    /// and wait for someone to unplug something.
    fn enumerate(&self) -> Result<Vec<DeviceDescriptor>, HotplugError>;

    /// Changes, in order, as they occur.
    fn watch(&self) -> Result<impl Iterator<Item = HotplugEvent>, HotplugError>;
}

// Implementation note, not yet code: UdevSource wraps tokio_udev's
// MonitorBuilder over the usb, block, sound, and video4linux subsystems. The
// descriptor's `speed_mbps` comes from the parent USB device's `speed`
// attribute and `driver` from the bound-driver link. Both live on the
// descriptor rather than being looked up on demand because they are the two
// fields that answer "why isn't my thing working", and an agent cannot ask for
// a field it does not know exists. The udev and tokio-udev dependencies are
// added when this lands, not before.
