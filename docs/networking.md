# Networking on Null Server

Installed systems use **systemd-networkd** with **systemd-resolved** (no NetworkManager). Every wired port (`en*`, `eth*`) gets DHCP for IPv4 and IPv6 out of the box: `/etc/systemd/network/80-null-dhcp.network`. The live USB is networked by live-config (ifupdown + dhclient) instead.

`networkctl status`, `resolvectl status`, `sudo networkctl reload` after a change.

## Static address

Create `/etc/systemd/network/10-eno1.network` (lower number wins over the DHCP file for that port):

```ini
[Match]
Name=eno1

[Network]
Address=10.0.0.20/24
Gateway=10.0.0.1
DNS=10.0.0.1
```
Then `sudo networkctl reload`.

## VLANs and bridges

```ini
# /etc/systemd/network/20-vlan30.netdev
[NetDev]
Name=vlan30
Kind=vlan
[VLAN]
Id=30

# /etc/systemd/network/10-eno1.network
[Match]
Name=eno1
[Network]
VLAN=vlan30
DHCP=yes

# /etc/systemd/network/20-vlan30.network
[Match]
Name=vlan30
[Network]
DHCP=yes
```
A bridge is the same shape with `Kind=bridge` and `Bridge=br0` on the member port (`man systemd.netdev`).

## Firewall

`null-fw status`, `null-fw allow 443`, `null-fw allow 51820/udp`, `null-fw deny 443`. Rules in `/etc/nftables.conf`, ports in `/etc/nftables.d/null-ports.nft`. Forwarding is open so containers and VPNs work; set the forward chain to `policy drop` in `/etc/nftables.conf` if this box must never route.

## Serial console

115200 8N1 on the first serial port (`ttyS0` on amd64, `ttyAMA0` on arm64), with GRUB on it too. `picocom -b 115200 /dev/ttyUSB0` from another box.
