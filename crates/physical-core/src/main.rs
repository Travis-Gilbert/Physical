//! The Physical daemon.
//!
//! Headless. Holds the catalog, routes hotplug events to modules by
//! capability, and serves HTTP/WS to clients that do the actual playing and
//! rendering.

#![forbid(unsafe_code)]

fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "physical_core=info".into()),
        )
        .init();

    tracing::info!(
        contract = physical_contracts::CONTRACT_VERSION,
        "physical-core: scaffold, nothing implemented"
    );
}
