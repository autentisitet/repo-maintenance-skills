# Container Platform Compatibility

## Ubuntu and Fedora

- Detect the distribution and available package manager; do not assume only `apt` or only `dnf`.
- Use `docker compose` for Docker and an explicitly detected `podman compose` or `podman-compose` for Podman. Do not hide runtime differences behind shell aliases.
- On Ubuntu, inspect AppArmor, ownership, and rootless paths. On Fedora, test under SELinux Enforcing with UID/GID mappings, Unix sockets, and device access.

---

## SELinux and Mounts

- Prefer named volumes. For host bind mounts, use `:Z` for private relabeling and `:z` only when several containers genuinely share the path.
- Diagnose labels, container users, rootless UID/GID mappings, and mount options before changing permissions.
- Do not solve mount failures by disabling SELinux, using `--privileged`, or recursively broadening permissions without a boundary.
- Keep operational forwarding on loopback or controlled tunnels; do not publish Redis or database ports publicly.

---

## CPU and GPU

- CPU is the default and must not require a GPU runtime or device declaration.
- Keep Docker and Podman GPU device, runtime, CDI, and hook differences in their respective override files.
- Test GPU combinations only on hosts with the required hardware, drivers, and integration. Report unavailable hardware as untested rather than treating configuration parsing as proof.

---

## Runtime Verification

Build the root `Dockerfile` with each target runtime. When possible, start at least one CPU combination on Ubuntu and Fedora Enforcing, then inspect health, internal network isolation, bind mounts, rootless permissions, restart behavior, and shutdown data integrity.
