# Networking on Null Server

ifupdown, no NetworkManager. Every wired port (`en*`, `eth*`) gets DHCP for IPv4 and IPv6 out of the box (`/etc/network/interfaces.d/auto-dhcp`).

## Static address

Create `/etc/network/interfaces.d/eno1` (and delete the matching pattern line in `auto-dhcp` if you want to be tidy):

```
auto eno1
iface eno1 inet static
    address 10.0.0.20/24
    gateway 10.0.0.1
    dns-nameservers 10.0.0.1
```
Then `sudo ifdown eno1; sudo ifup eno1`. (`dns-nameservers` needs the `resolvconf` package; without it, edit `/etc/resolv.conf`.)

## VLANs and bridges

`vlan` and `bridge-utils` are installed:

```
auto eno1.30
iface eno1.30 inet dhcp

auto br0
iface br0 inet dhcp
    bridge_ports eno1
```

## Firewall

`null-fw status`, `null-fw allow 443`, `null-fw allow 51820/udp`, `null-fw deny 443`. Rules in `/etc/nftables.conf`, ports in `/etc/nftables.d/null-ports.nft`. Forwarding is open so containers and VPNs work; set the forward chain to `policy drop` in `/etc/nftables.conf` if this box must never route.

## Serial console

115200 8N1 on the first serial port (`ttyS0` on amd64, `ttyAMA0` on arm64), with GRUB on it too. `picocom -b 115200 /dev/ttyUSB0` from another box.
