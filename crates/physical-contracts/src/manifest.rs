//! Module manifests.
//!
//! A manifest is the entire interface between the core and a module. The core
//! reads it, decides what the module may reach, and routes devices to it. It
//! never reads a module's code to work out what the module wants.

use crate::capability::{Capability, Permission};
use serde::{Deserialize, Serialize};

/// A module's declaration of itself.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct ModuleManifest {
    /// Reverse-DNS identifier. Unique across the registry.
    pub id: String,
    /// Display name.
    pub name: String,
    /// Semantic version of this module.
    pub version: String,
    /// One sentence describing what it does.
    pub description: String,
    /// Module contract version this manifest targets.
    pub contract: String,
    /// Capabilities this module can bind to.
    #[serde(default)]
    pub consumes: Vec<Capability>,
    /// Capabilities this module offers to others.
    #[serde(default)]
    pub provides: Vec<Capability>,
    /// Grants this module requires. An operator sees this list before install.
    #[serde(default)]
    pub permissions: Vec<Permission>,
    /// Where the source lives. Required: a module with no published source is
    /// not installable from the first-party registry.
    pub source: String,
    /// SPDX license expression.
    pub license: String,
}

impl ModuleManifest {
    /// Whether this module can bind to `offered`.
    #[must_use]
    pub fn accepts(&self, offered: &Capability) -> bool {
        self.consumes.iter().any(|wanted| match (wanted, offered) {
            // A vendor grant with no product matches any product from that
            // vendor; every other pair is exact.
            (
                Capability::UsbVendor { vendor, product: None },
                Capability::UsbVendor { vendor: offered_vendor, .. },
            ) => vendor == offered_vendor,
            _ => wanted == offered,
        })
    }
}

/// A module bound to a device.
#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct Binding {
    /// The module holding this binding.
    pub module_id: String,
    /// The device's sysfs path.
    pub syspath: String,
    /// The capability the match was made on. Recorded so an operator can be
    /// told *why* a module claimed a device, not only that it did.
    pub matched: Capability,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capability::UsbClass;

    fn manifest(consumes: Vec<Capability>) -> ModuleManifest {
        ModuleManifest {
            id: "dev.physical.test".into(),
            name: "Test".into(),
            version: "0.1.0".into(),
            description: "Fixture.".into(),
            contract: "0.1".into(),
            consumes,
            provides: Vec::new(),
            permissions: Vec::new(),
            source: "https://example.invalid/test".into(),
            license: "Apache-2.0".into(),
        }
    }

    #[test]
    fn a_class_consumer_accepts_any_device_of_that_class() {
        let module = manifest(vec![Capability::Usb { class: UsbClass::Video }]);
        assert!(module.accepts(&Capability::Usb { class: UsbClass::Video }));
        assert!(!module.accepts(&Capability::Usb { class: UsbClass::Audio }));
    }

    #[test]
    fn a_vendor_wildcard_accepts_any_product_from_that_vendor() {
        let module = manifest(vec![Capability::UsbVendor { vendor: 0x1d6b, product: None }]);
        assert!(module.accepts(&Capability::UsbVendor {
            vendor: 0x1d6b,
            product: Some(0x0003),
        }));
        assert!(!module.accepts(&Capability::UsbVendor {
            vendor: 0x0bda,
            product: Some(0x0003),
        }));
    }
}
