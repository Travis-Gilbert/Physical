//! The capability vocabulary.
//!
//! A capability is what a module binds to, never what a device *is*. Physical
//! ships no device database and no vendor/product table. Binding happens
//! against the class a device claims at enumeration time, which is why a module
//! written today can accept hardware released years from now.

use serde::{Deserialize, Serialize};
use std::fmt;

/// A USB device class as claimed at enumeration.
///
/// These are the classes for which Linux already provides drivers, which is the
/// whole reason unknown hardware works without configuration. The set is
/// deliberately not exhaustive: unrecognised classes surface as
/// [`UsbClass::Other`] so an operator can see them rather than having them
/// silently dropped.
#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum UsbClass {
    /// Mass Storage / UAS. Drives, sticks, cartridge readers.
    MassStorage,
    /// USB Video Class. Capture devices, cameras.
    Video,
    /// USB Audio Class. DACs, microphones, interfaces.
    Audio,
    /// Printer class. Pairs with IPP Everywhere for driverless printing.
    Printer,
    /// Still Image (PTP/MTP). Cameras and phones.
    StillImage,
    /// Human Interface Device.
    Hid,
    /// Communications Device Class. Serial and network gadgets.
    Communications,
    /// Class is declared per-interface rather than per-device.
    PerInterface,
    /// Vendor-specific. Requires a module that names the vendor explicitly.
    VendorSpecific,
    /// A class code this build does not recognise, retained verbatim.
    Other(u8),
}

impl UsbClass {
    /// Map a raw USB base class code to a known class.
    #[must_use]
    pub const fn from_code(code: u8) -> Self {
        match code {
            0x00 => Self::PerInterface,
            0x01 => Self::Audio,
            0x02 => Self::Communications,
            0x03 => Self::Hid,
            0x06 => Self::StillImage,
            0x07 => Self::Printer,
            0x08 => Self::MassStorage,
            0x0e => Self::Video,
            0xff => Self::VendorSpecific,
            other => Self::Other(other),
        }
    }

    /// Whether a module may bind to this class without naming a vendor.
    ///
    /// Vendor-specific devices are excluded because binding to them without an
    /// explicit vendor declaration would be a guess, and a wrong guess against
    /// unknown hardware is worse than no binding at all.
    #[must_use]
    pub const fn is_generically_bindable(self) -> bool {
        !matches!(self, Self::VendorSpecific | Self::Other(_) | Self::PerInterface)
    }
}

/// Something a module consumes or provides.
#[derive(Clone, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "kebab-case")]
pub enum Capability {
    /// Any device enumerating as this USB class.
    Usb {
        /// The class to bind against.
        class: UsbClass,
    },
    /// A device from a named vendor, for hardware with no standard class.
    ///
    /// Required for [`UsbClass::VendorSpecific`]. Deliberately more awkward
    /// than class binding so that class binding stays the default.
    UsbVendor {
        /// USB vendor ID.
        vendor: u16,
        /// USB product ID, or `None` for any product from this vendor.
        product: Option<u16>,
    },
    /// An optical drive presenting an audio CD.
    OpticalAudioDisc,
    /// A block device the core has admitted as vault storage.
    VaultVolume,
    /// A removable cartridge in the front slot.
    Cartridge,
    /// A printer reachable over IPP, discovered via mDNS.
    IppPrinter,
    /// A named service offered by another module. The string is the service
    /// name; resolution is the registry's job, not the caller's.
    Service(String),
}

impl fmt::Display for Capability {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Usb { class } => write!(f, "usb:{class:?}"),
            Self::UsbVendor { vendor, product } => match product {
                Some(product) => write!(f, "usb-vendor:{vendor:04x}:{product:04x}"),
                None => write!(f, "usb-vendor:{vendor:04x}:*"),
            },
            Self::OpticalAudioDisc => f.write_str("optical:audio-disc"),
            Self::VaultVolume => f.write_str("vault:volume"),
            Self::Cartridge => f.write_str("vault:cartridge"),
            Self::IppPrinter => f.write_str("net:ipp-printer"),
            Self::Service(name) => write!(f, "service:{name}"),
        }
    }
}

/// What a module is permitted to reach.
///
/// Grants are explicit and additive. A module with no grants can compute and
/// respond, and nothing else.
#[derive(Clone, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum Permission {
    /// Read catalog nodes matching a label.
    GraphRead {
        /// The node label this grant covers.
        label: String,
    },
    /// Write catalog nodes under a label the module owns.
    GraphWrite {
        /// The node label this grant covers.
        label: String,
    },
    /// Read bytes from vault storage.
    VaultRead,
    /// Write bytes to vault storage.
    VaultWrite,
    /// Reach the network outside the local subnet.
    NetworkEgress,
    /// Invoke the configured agent endpoint.
    AgentInvoke,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn known_class_codes_map_to_named_variants() {
        assert_eq!(UsbClass::from_code(0x0e), UsbClass::Video);
        assert_eq!(UsbClass::from_code(0x08), UsbClass::MassStorage);
        assert_eq!(UsbClass::from_code(0x07), UsbClass::Printer);
    }

    #[test]
    fn unknown_class_codes_are_retained_verbatim() {
        assert_eq!(UsbClass::from_code(0x42), UsbClass::Other(0x42));
    }

    #[test]
    fn vendor_specific_devices_are_not_generically_bindable() {
        assert!(!UsbClass::VendorSpecific.is_generically_bindable());
        assert!(UsbClass::Video.is_generically_bindable());
    }
}
