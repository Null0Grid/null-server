# Null Server — Design

The decisions behind Null Server 1.0.0. Change this file first, then the build.

## Identity

| | |
|---|---|
| Name | **Null Server**, part of the Null Grid family (Systems) |
| Base | Debian 13 "trixie" (stable), stock Debian kernel, no modified packages |
| Target | Headless: homelab boxes, Proxmox/KVM guests, ZimaBoard/Pi-class ARM boards, a USB stick used as a small server |
| Relation to Null OS | Same base, same terminal, same repo layout; everything graphical removed, server pieces added. Not a third Null OS edition: its own repo and version line, because the installer, boot and defaults are different enough |
| Look | Neon Lab in the terminal only: cyan `#00e5ff` for keys and frames, pink `#ff2e88` for the user and titles, the path in bold cyan (no green: two colours only), red only for errors and root |

## What's deliberately not here

No desktop, display manager, Plymouth, Calamares, Flatpak, PipeWire, icon theme or wallpaper. No NetworkManager (systemd-networkd with DHCP on every wired port; static addresses go in `/etc/systemd/network/`). No Wi-Fi firmware by default (a server has a cable; `apt install firmware-iwlwifi` if not). No mail. No NULL // PLAY, no Tyler.

## Terminal and shell

Carried over from Null OS unchanged, by design: `.zshrc`, `patch-font.py`, `null-mark.py`, the fastfetch logo and colours.

| | |
|---|---|
| Shell | zsh for every user, autosuggestions and syntax highlighting |
| Prompt | Kali-style two lines: `┌──(user<mark>host)-[path]-[branch]-[✗ code]` / `└─$`; red frame and `#` for root |
| The mark | U+E900 in Null Mono (JetBrains Mono patched at build time). The TTF ships at `/usr/share/fonts/truetype/null-mono/` for the SSH client machine; `null-font` explains |
| Over SSH | The prompt falls back to `@` unless the client sends `NULL_GLYPH=1` and `COLORTERM` (sshd accepts both). Null OS has the font already and only needs `SendEnv` in `~/.ssh/config` |
| Console | `@` fallback, 256 colours (the Linux console has no truecolor) |
| fastfetch | Same logo, colours and layout; DE/WM/theme/icons/font lines replaced by Services, Roles and Null Drive |
| MOTD | One static line in `/etc/motd`; a dynamic block from `/etc/update-motd.d/10-null` (name, kernel, host, IP, uptime, load, memory, disk, failed services, pending updates (cached 6 h), Null Drive status, reboot-required). Red only when something is wrong |
| `null-info` | Same as Null OS plus open ports, roles and Null Drive |

## Boot and console

| | |
|---|---|
| Boot menu (ISO) | Null Server splash (mark + "NULL SERVER" in Silkscreen), cyan highlight |
| Live session | `user`/`live`, autologin on tty1 (wrapper `null-getty` only does that when `boot=live`), passwordless sudo, persistence supported |
| Serial | `console=ttyS0,115200 console=tty0` on amd64, `ttyAMA0` on arm64, on the live ISO and in GRUB on installed systems (`GRUB_TERMINAL="console serial"`); systemd adds a login on the serial port automatically |
| GRUB | 3-second timeout, `quiet`, no splash, Null Server as distributor |
| First boot | `null-firstboot`: regenerates SSH host keys and machine-id (clones and images never share an identity), grows `/` into the disk (growpart + resize2fs/xfs_growfs/btrfs) |

## Security defaults

| | |
|---|---|
| SSH | On. `PermitRootLogin no`, password auth on until a key is given (then off), `MaxAuthTries 4`, no X11, `UseDNS no`, `AcceptEnv NULL_GLYPH COLORTERM` |
| Firewall | nftables, on by default. Input: lo, established, ICMP/ICMPv6, DHCPv6, then the sets in `/etc/nftables.d/null-ports.nft` (TCP 22, 8080; UDP 5353 for Null Drive's mDNS), SSH brute-force brake (10 new connections/minute per address), drop. Forward **accept** on purpose so Docker, Podman, libvirt and WireGuard keep working. `null-fw` edits the port file and reloads |
| Updates | `unattended-upgrades` for security, `needrestart` restarts services on its own |
| Root | Locked after install; sudo via the first user |

## Null Drive

The one app the box is made for. Not pre-installed (it has its own release cadence and the ISO stays Debian-only), but one command away and everything around it is ready:

- `null-drive install` → latest `nulldrive_<v>_<arch>.deb` from Null0Grid/null-drive releases, SHA256 checked against the release's `SHA256SUMS.txt`, installed, enabled, firewall port opened
- Port 8080 open from the start; `null-drive port <n>` moves it and the firewall follows
- Status in fastfetch, the MOTD and `null-info`, with the URL to paste into the Null Grid browser (Settings → Drive)
- `nulldrive` is also a role, so the installer and `null-extras` can do it
- Reverse proxy role (Caddy) for HTTPS in front of it

## Installer

`null-install`, a bash + whiptail script in the live session (no Calamares, no d-i):

- Whole disk, GPT: BIOS boot stub (amd64) + 512 MB EFI + root (ext4 default, xfs/btrfs optional). GRUB installed for UEFI (plus the removable-media fallback path) and BIOS, so the disk boots on either firmware
- Copies the live squashfs with rsync, removes the live-only packages, makes the user (sudo, zsh), hostname, hosts, fstab by UUID, Debian mirrors back in apt, systemd-networkd with DHCP on every wired port
- Roles chosen at install time are written to `/var/lib/null-server/roles-pending` and installed by `null-roles-pending.service` on the first boot with internet
- Unattended: `null.autoinstall=<url | /dev/disk/by-label/NULLCFG | path>` on the kernel line; the answers file uses `NULL_DISK=`, `NULL_HOSTNAME=`, `NULL_USER=`, `NULL_PASSWORD=`, `NULL_SSH_KEY=`, `NULL_ROLES=`, `NULL_FS=`, `NULL_TIMEZONE=`, `NULL_REBOOT=`
- Log: `/var/log/null-install.log`

## Roles (`null-extras`)

Same command and data format as the Null OS Extras (`group|title|description|repo|packages|post`), server groups, no GUI. Each `post` step opens the firewall ports, adds the first user to the right group and enables the service. Third-party repos (Tailscale, Kubernetes, HashiCorp) are added only when their role is installed.

## Build and release

- live-build, `--debian-installer none`, recommends off, firmware in; `build.sh` + `auto/config`, same as Null OS
- amd64 (BIOS + UEFI hybrid ISO) and arm64 (UEFI), built natively on GitHub's runners
- Versioning starts at 1.0.0, independent of Null OS
- CI test: boot the ISO in QEMU, screenshot the console, run `null-install` onto a virtual disk, reboot, log in on the console and over SSH, publish screenshots and the SSH transcript to `screenshots-<arch>`

## Open

- Pi/SBC SD-card images (not an ISO; needs a different image type with the board's firmware partition). The first-boot growth is already there for them
- Cloud images (qcow2/raw with cloud-init) for Proxmox templates
- Null OS: add `SendEnv NULL_GLYPH COLORTERM` to its default `~/.ssh/config` so the mark shows when SSHing into a Null Server
