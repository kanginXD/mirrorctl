# mirrorctl

Control DNF 4/5 mirrors with simple commands.

**WARNING:** Still in development. Interfaces and behavior may change without notice.

## Features

- Supported distro:
  - Fedora
  - AlmaLinux (TODO)
  - Rocky Linux (TODO)
- Supported third-party repositories (configure with `--group`):
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

### `auto` — automatic mirror selection (metalink / GeoIP)

```bash
# default
sudo mirrorctl auto

# prefer countries
sudo mirrorctl auto --country KR --country US

# prefer protocols
sudo mirrorctl auto --protocol https --protocol rsync

# skip availability check
sudo mirrorctl auto --country KR --protocol https --no-check
```

- `--country` and `--protocol` are only preferences; another mirror can still
  win. Use `pin` instead to pin exact base URLs.
- Country codes: [ISO 3166-1 Alpha-2 (two letters)](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements); repeat `--country` for each.
- When `--country` or `--protocol` is set, mirror availability is checked before
  write (skip with `--no-check`).

### `pin` — fixed mirror URLs or main-repository only

Use one mode only:

- **`--url` / `--file`** — fixed mirror base URL list (`--url` may be repeated). Not
  together with `--official-only`.
- **`--official-only`** — main-repository URLs only (no volunteer mirror network).
  Cannot be combined with `--url` or `--file`. Works with `--group`.

#### Single URL

```bash
sudo mirrorctl pin --url https://dl.fedoraproject.org/pub/fedora/linux
```

#### Multiple URLs

```bash
sudo mirrorctl pin \
  --url https://dl.fedoraproject.org/pub/fedora/linux \
  --url https://download-ib01.fedoraproject.org/pub/fedora/linux
```

#### From a file

One mirror base URL per line in `mirrors.txt` (`#` starts a comment).

**Example `mirrors.txt`**

```text
https://dl.fedoraproject.org/pub/fedora/linux
https://download-ib01.fedoraproject.org/pub/fedora/linux
```

**Run**

```bash
sudo mirrorctl pin --file ./mirrors.txt
```

#### Main-repository only

Run once per `--group` you need:

```bash
sudo mirrorctl pin --official-only
sudo mirrorctl pin --official-only --group rpmfusion-free
sudo mirrorctl pin --official-only --group rpmfusion-nonfree
```

### `init-empty` — initialize empty mirror settings

Writes empty mirror overrides for repos mirrorctl manages so DNF cannot
auto-pick mirrors. You must set mirrors explicitly afterward.

```bash
sudo mirrorctl init-empty
```

### `reset` — delete all mirrorctl overrides and revert back

This command deletes mirrorctl's override file (`/etc/dnf/repos.override.d/999-mirrorctl.repo`).

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

Supported on: `auto`, `pin` (including `pin --official-only`).

```bash
sudo mirrorctl auto --group rpmfusion-free
sudo mirrorctl pin --url https://download1.rpmfusion.org --group rpmfusion-free
sudo mirrorctl pin --official-only --group rpmfusion-nonfree
```

## After changing overrides

DNF should refresh cached repo metadata to pick up the new override file.

```bash
sudo mirrorctl refresh
```

Or manually:

```bash
sudo dnf clean all && sudo dnf makecache --refresh
```

You can also use `sudo dnf repo info --all` after cleaning to inspect repos.
