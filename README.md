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
- One override file: `/etc/dnf/repos.override.d/999-mirrorctl.repo`
- Undo in one step: `mirrorctl reset`

## Install

```bash
uv tool install "git+https://github.com/kanginXD/mirrorctl.git"
```

Run with:

```bash
mirrorctl --help
```

## Commands

### Auto mirrors (GeoIP-based auto selection)

```bash
# default (GeoIP)
sudo mirrorctl auto-mirrors

# prefer countries
sudo mirrorctl auto-mirrors --country KR --country US

# prefer protocols
sudo mirrorctl auto-mirrors --protocol https --protocol rsync

# skip availability check
sudo mirrorctl auto-mirrors --country KR --protocol https --no-check
```

- `--country` and `--protocol` are only preferences; another mirror can still
  win. Use `pin-mirrors` instead to ensure specific mirrors are used.
- Country codes: [ISO 3166-1 Alpha-2 (two letters)](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements); repeat `--country` for each.
- When `--country` or `--protocol` is set, mirror availability is checked before
  write (skip with `--no-check`).

### Pin exact mirrors

Use either `--url` (repeat for multiple) or `--file`, not both.

Single URL:
```bash
sudo mirrorctl pin-mirrors --url https://dl.fedoraproject.org/pub/fedora/linux
```

Multiple URLs:
```bash
sudo mirrorctl pin-mirrors \
  --url https://dl.fedoraproject.org/pub/fedora/linux \
  --url https://download-ib01.fedoraproject.org/pub/fedora/linux
```

From file (`mirrors.txt`: one URL per line; `#` starts a comment line):

```text
https://dl.fedoraproject.org/pub/fedora/linux
https://download-ib01.fedoraproject.org/pub/fedora/linux
```

```bash
sudo mirrorctl pin-mirrors --file ./mirrors.txt
```

### Official-only (disable mirror networks)

Run once per group you want to apply:

```bash
sudo mirrorctl official-only
sudo mirrorctl official-only --group rpmfusion-free
sudo mirrorctl official-only --group rpmfusion-nonfree
```

### Block automatic mirror selection for all managed groups

Blocks DNF automatic mirror selection for mirrorctl-managed repos; nudges the
user toward explicit mirror setup.

```bash
sudo mirrorctl unset-all-mirrors
```

### Reset mirrorctl override

Undo mirrorctl's own override (`/etc/dnf/repos.override.d/999-mirrorctl.repo`).

```bash
sudo mirrorctl reset
```

### The `--group` option

| When | What mirrorctl changes |
|------|-------------------------|
| *(omit flag)* | The **default OS repository bundle** (repos for your distro) |
| `--group rpmfusion-free` | **RPM Fusion free** repos only |
| `--group rpmfusion-nonfree` | **RPM Fusion nonfree** repos only |

RPM Fusion uses a **different mirror pool** than your OS repositories (different
metalink server and paths). Without `--group`, only the OS bundle is updated;
RPM Fusion repos are left unchanged until you run the same command again with
the right `--group`.

Supported on: `auto-mirrors`, `pin-mirrors`, `official-only`.

```bash
sudo mirrorctl auto-mirrors --group rpmfusion-free
sudo mirrorctl pin-mirrors --url https://download1.rpmfusion.org --group rpmfusion-free
sudo mirrorctl official-only --group rpmfusion-nonfree
```

### After any command

DNF must refresh cached repo metadata to pick up the new override file.

```bash
sudo mirrorctl refresh-cache
```

Or manually:

```bash
sudo dnf clean all && sudo dnf makecache --refresh
```

You can also use `sudo dnf repo info --all` after cleaning to inspect repos.
