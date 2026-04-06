# mirrorctl

Control DNF 4/5 mirrors with simple commands.

## Features

- Supported distro:
  - Fedora
  - AlmaLinux (TODO)
  - Rocky Linux (TODO)
- Supported external groups:
  - RPM Fusion free (`rpmfusion-free`)
  - RPM Fusion nonfree (`rpmfusion-nonfree`)
- All mirrorctl commands write to one override file:
  `/etc/dnf/repos.override.d/999-ultimate.repo`
- Instant reset to defaults

## Install

```bash
uvx tool install "git+https://github.com/kanginXD/mirrorctl.git"
```

Run with:

```bash
mirrorctl --help
```

## Commands

### Auto mirrors (metalink; GeoIP-based auto selection)

`auto-mirrors` keeps DNF on metalink mode and lets the mirror network choose
servers automatically (GeoIP-based).

`--country` and `--protocol` are preferences, not strict pinning. At runtime,
another mirror can still be selected if the mirror network decides so.

If you need strict control (for security/compliance), use `pin-mirrors`
instead of `auto-mirrors`.

Country code format:

- ISO 3166-1 Alpha-2
- Two letters per code (e.g. `KR`, `US`, `DE`)
- Repeat the flag for multiple countries

By default, mirrorctl checks mirror availability for requested
country/protocol preferences before writing config.
Use `--no-check` to skip this validation.

```bash
# Basic
sudo mirrorctl auto-mirrors

# Country preference (repeat --country)
sudo mirrorctl auto-mirrors --country KR --country US

# Protocol preference
sudo mirrorctl auto-mirrors --protocol https --protocol rsync

# Skip availability check (with preferences)
sudo mirrorctl auto-mirrors --country KR --protocol https --no-check
```

### Pin exact mirrors (baseurl only)

Single URL:
```bash
sudo mirrorctl pin-mirrors https://dl.fedoraproject.org/pub/fedora/linux
```

Multiple URLs:
```bash
sudo mirrorctl pin-mirrors \
  https://dl.fedoraproject.org/pub/fedora/linux \
  https://download-ib01.fedoraproject.org/pub/fedora/linux
```

From file:
`mirrors.txt`:
```text
https://dl.fedoraproject.org/pub/fedora/linux
https://download-ib01.fedoraproject.org/pub/fedora/linux
```

```bash
sudo mirrorctl pin-mirrors $(xargs -a mirrors.txt)
```

External group (e.g. RPM Fusion):
```bash
sudo mirrorctl pin-mirrors \
  https://download1.rpmfusion.org \
  --group rpmfusion-free
```

### Official-only (disable mirror networks)

Run once per group you want to apply:

```bash
sudo mirrorctl official-only
sudo mirrorctl official-only --group rpmfusion-free
sudo mirrorctl official-only --group rpmfusion-nonfree
```

### Block automatic mirror selection for all managed groups

```bash
sudo mirrorctl unset-all-mirrors
```

### Reset mirrorctl override

Delete mirrorctl's override file and return to repository defaults.

```bash
sudo mirrorctl reset
```

### Apply to External group

Use `--group` for external repositories such as RPM Fusion.
They typically use different mirror pools, so you must configure them separately.
```bash
sudo mirrorctl auto-mirrors --group rpmfusion-free
sudo mirrorctl official-only --group rpmfusion-nonfree
```

### After any command

DNF must refresh cached repo metadata to pick up the new override file.

```bash
sudo dnf clean all && sudo dnf repo info --all
```
