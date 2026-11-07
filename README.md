# Null Server

Null OS for servers: Debian 13 (trixie), no desktop, the same terminal. A live USB that boots to a shell in seconds, installs to a disk in a few minutes (or unattended), and comes ready for Null Drive. Stock Debian underneath, no modified packages, security updates straight from Debian.

```
┌──(luc⦻grid)-[~]
└─$ null-drive install
```
*(The real prompt uses the Null mark from Null Mono, exactly like Null OS. On the text console and over SSH it falls back to `@`; `null-font` explains how to get the mark back over SSH.)*

Every design decision is in **[DESIGN.md](DESIGN.md)**. Screenshots from the latest CI build are on the [`screenshots-amd64`](../../tree/screenshots-amd64) and [`screenshots-arm64`](../../tree/screenshots-arm64) branches.

## What's in it

- **Terminal:** the Null OS one, unchanged: zsh with the two-line Kali-style prompt, autosuggestions, syntax highlighting, Neon Lab colours, fastfetch with the Null mark. Null Mono (JetBrains Mono + the mark) is on the box for the machine you SSH from.
- **Server defaults:** SSH on (no root login, brute-force brake), nftables firewall on (only **22** and **8080** open), serial console on, `unattended-upgrades`, chrony, `qemu-guest-agent`, a dynamic MOTD (IP, load, disk, failed services, pending updates, Null Drive status), fresh host keys and machine-id on first boot, root filesystem grows into the disk.
- **Null Drive ready:** `null-drive install` fetches the latest release `.deb` for your architecture, checks its SHA256, starts it on :8080 (already open in the firewall) and prints the URL to put in the Null Grid browser's Drive settings. `null-drive update|status|port|logs|remove`.
- **Roles** (`null-extras`): nulldrive, containers (Docker + Podman), proxy (Caddy), nas (Samba + NFS), vpn (WireGuard + Tailscale), monitoring (node exporter), homelab (Ansible, kubectl, Terraform), network (nmap, tshark, arp-scan…), virt (QEMU/KVM headless), backup (restic, borg, rclone), dev, claude (Claude Code). Each role opens its ports and enables its services. Nothing is pre-baked: a role downloads when you ask.
- **Installer:** `sudo null-install` — pick a disk, hostname, user, password, optional SSH key (password login over SSH turns off when you give one) and roles. Boots on UEFI and BIOS (amd64) or UEFI (arm64). Unattended: `null.autoinstall=http://…/answers.conf` on the kernel line ([docs/unattended.md](docs/unattended.md)).
- **Network toolkit** on every box: tcpdump, mtr, iperf3, dig, ethtool, WireGuard tools, lldpd, minicom, picocom.
- **Size:** about 700 MB ISO; a fresh install uses about 2 GB.

Live session login: `null` / `null`, logged in automatically on tty1, passwordless sudo. Installed systems use the account you create.

## Get the ISO

Every push to `main` builds both architectures on GitHub Actions:

1. Open **Actions → Build Null Server → latest run**.
2. Download **null-server-iso-amd64** or **null-server-iso-arm64**.

Tagging a release (`v1.1.0` or `1.1.0`) attaches both ISOs to the GitHub Release; for a release made by hand, Actions → Build Null Server → Run workflow → type the tag.

## Put it on a USB stick

```
sudo tools/make-usb.sh nullserver-1.1.0-trixie-amd64.iso /dev/sdX
```
That also adds a `persistence` partition, so you can use the stick itself as a tiny server that keeps its changes. A plain `dd` or balenaEtcher works too.

## Install

Boot the stick, then:

```
sudo null-install
```
or, with no questions:
```
sudo null-install --disk /dev/sda --hostname grid --user luc --password '…' \
     --ssh-key 'ssh-ed25519 AAAA…' --roles nulldrive,containers --yes
```
Reboot, remove the stick, `ssh luc@grid`. Roles you picked install on the first boot with internet.

## Commands

| Command | Does |
|---|---|
| `null-info` | one-screen summary (what the MOTD shows, plus CPU/addresses) |
| `null-extras list` / `install <role>` | roles |
| `null-drive install` / `status` / `update` | Null Drive |
| `null-fw status` / `allow 443` / `deny 443` / `off` | firewall |
| `null-install` | put Null Server on a disk (live session) |
| `null-font` | get Null Mono onto the machine you SSH from |

## Build it yourself

| Host | Command |
|---|---|
| Debian 12/13 | `sudo ./build.sh` (`ARCH=arm64 sudo -E ./build.sh` for ARM) |
| Any Linux with Docker | `./docker-build.sh` |

A build takes 20–40 minutes and needs about 8 GB of free disk.

## Testing

Every build boots the ISO in QEMU (`tools/vm-test.py`), screenshots the console, runs `null-install` onto a virtual disk, reboots into it, logs in on the console and over SSH, and publishes the screenshots and the SSH transcript to the `screenshots-<arch>` branch.

## Customize

| Want to change | Edit |
|---|---|
| Name, version, Debian release | `null-server.conf` |
| Packages | `config/package-lists/*.list.chroot` |
| Prompt and shell | `config/includes.chroot/etc/skel/.zshrc` (same file as Null OS) |
| fastfetch | `config/includes.chroot/etc/xdg/fastfetch/config.jsonc` |
| MOTD | `config/includes.chroot/etc/update-motd.d/10-null` |
| Firewall | `config/includes.chroot/etc/nftables.conf` and `nftables.d/null-ports.nft` |
| Roles | `GROUPS_DATA` in `config/includes.chroot/usr/local/bin/null-extras` |
| SSH | `config/includes.chroot/etc/ssh/sshd_config.d/10-null-server.conf` |
| Boot splash | `tools/make-branding.py` |

## Relation to Null OS

Null OS (desktop) and Null Server share the Debian base, the terminal files and the build layout, in two repos: [Null0Grid/null-os](https://github.com/Null0Grid/null-os) and this one. When the prompt or fastfetch changes in one, copy the file to the other.
