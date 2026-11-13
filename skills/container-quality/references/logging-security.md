# Logging and Build Security

## Persistent Logs and Rotation

Send long-running service stdout/stderr to a persistent container logging driver with bounded rotation. Define shared logging in the base Compose file and attach it explicitly:

```yaml
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "5"

services:
  api:
    logging: *default-logging
```

Adjust limits to log volume and disk budget, but never allow unbounded growth. If the application also writes files, rotate those files and avoid uncontrolled duplication with container stdout.

Docker and Podman may use different logging backends. Inspect the merged configuration and actual runtime driver, then generate enough non-sensitive test output to verify persistence, rotation, and bounded disk use.

---

## Build Context

- Build both runtimes from repository root, for example `docker build -f Dockerfile .` and `podman build -f Dockerfile .`.
- Exclude secrets, VCS metadata, local environments, datasets, model weights, test output, and unrelated artifacts in `.dockerignore`.
- Do not copy the whole repository and delete sensitive content later. Restrict the context first and copy only required files per build stage.

---

## Secrets and Privileges

- Do not place passwords, tokens, private keys, or real environment files in Dockerfiles, Compose files, image layers, or build arguments. Use runtime secret mechanisms or controlled external injection.
- Do not use `--privileged` to hide device, mount, or permission errors. Grant only required capabilities, devices, and paths.
- Inspect image history and merged Compose output for sensitive values before delivery.
