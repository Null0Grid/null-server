# Null Server 1.0.0

Null OS for servers: Debian 13 (trixie), no desktop, the same terminal. First release.

- **Terminal:** the Null OS zsh prompt (cyan + pink), autosuggestions, syntax highlighting, fastfetch with the Null mark, Null Mono on the box for the machine you SSH from (`null-font`)
- **Null Drive ready:** `null-drive install` fetches the latest release, verifies it, starts it on :8080 (already open in the firewall)
- **Server defaults:** SSH (no root login, brute-force brake), nftables firewall (`null-fw`), serial console, unattended security updates, dynamic MOTD, fresh host keys and machine-id on first boot, root filesystem grows into the disk
- **Installer:** `sudo null-install` (interactive) or unattended with `null.autoinstall=` on the kernel line; UEFI + BIOS on amd64, UEFI on arm64
- **Roles:** `null-extras` — nulldrive, containers, proxy, nas, vpn, monitoring, homelab, network, virt, backup, dev, claude

Live session: `null` / `null`. Write the ISO with `tools/make-usb.sh` or any imaging tool.

| File | For |
|---|---|
| `nullserver-1.0.0-trixie-amd64.iso` | PCs, servers, Proxmox/KVM guests |
| `nullserver-1.0.0-trixie-arm64.iso` | UEFI ARM boards and VMs |

Tested in CI by booting each ISO in QEMU, installing to a disk, rebooting and logging in over SSH.
