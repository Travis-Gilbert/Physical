//! Device descriptors and hotplug events.
//!
//! A [`DeviceDescriptor`] is the whole diagnostic surface for "why isn't my
//! thing working". Every field here is something an operator or an agent would
//! reasonably ask about, which is why the descriptor carries negotiated speed
//! and bound driver rather than only identity.

use crate::capability::{Capability, UsbClass};
use serde::{Deserialize, Serialize};

/// A device as the kernel presents it.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct DeviceDescriptor {
    /// Stable sysfs path. The identity of this device while it is attached.
    pub syspath: String,
    /// Kernel subsystem (`usb`, `block`, `sound`, `video4linux`).
    pub subsystem: String,
    /// Device node under `/dev`, when one exists.
    pub devnode: Option<String>,
    /// USB vendor ID.
    pub vendor: Option<u16>,
    /// USB product ID.
    pub product: Option<u16>,
    /// Human-readable vendor string, when the device supplies one.
    pub vendor_name: Option<String>,
    /// Human-readable product string, when the device supplies one.
    pub product_name: Option<String>,
    /// Serial number, when the device supplies one.
    pub serial: Option<String>,
    /// Class claimed at enumeration.
    pub class: Option<UsbClass>,
    /// Driver the kernel bound, if any. `None` here is the single most common
    /// cause of a device that "does nothing".
    pub driver: Option<String>,
    /// Negotiated link speed in Mbit/s. A USB 3 device that negotiated 480 is
    /// on a bad cable or a USB 2 port, and this field is how that gets seen.
    pub speed_mbps: Option<u32>,
    /// Which expansion bay this device is behind, if it is behind one.
    pub bay: Option<BayId>,
}

impl DeviceDescriptor {
    /// The capability this device offers, if it can be bound generically.
    ///
    /// Returns `None` for vendor-specific and unrecognised classes. Those
    /// require a module that names the vendor, by design.
    #[must_use]
    pub fn generic_capability(&self) -> Option<Capability> {
        let class = self.class?;
        class
            .is_generically_bindable()
            .then_some(Capability::Usb { class })
    }

    /// Whether the kernel bound a driver to this device.
    #[must_use]
    pub fn has_driver(&self) -> bool {
        self.driver.is_some()
    }
}

/// Which expansion bay a device is behind.
///
/// Bays are numbered left to right from the front of the host. The number is a
/// physical fact about the enclosure, so an operator can be told "the card in
/// bay 3" rather than a sysfs path.
#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
pub struct BayId(pub u8);

/// A change in attached hardware.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(tag = "event", rename_all = "kebab-case")]
pub enum HotplugEvent {
    /// A device appeared.
    Added(DeviceDescriptor),
    /// A device went away. Carries the last known descriptor so consumers do
    /// not have to have cached one.
    Removed(DeviceDescriptor),
    /// A device changed in place: driver bound, media inserted, link
    /// renegotiated.
    Changed {
        /// State before the change.
        previous: DeviceDescriptor,
        /// State after the change.
        current: DeviceDescriptor,
    },
}

impl HotplugEvent {
    /// The descriptor this event concerns.
    #[must_use]
    pub fn descriptor(&self) -> &DeviceDescriptor {
        match self {
            Self::Added(device) | Self::Removed(device) => device,
            Self::Changed { current, .. } => current,
        }
    }
}
