# Unattended install

Boot the Null Server ISO with `null.autoinstall=<where the answers are>` on the kernel line (press Tab on the boot menu entry, or set it in your PXE/iPXE config). The live session fetches the answers, runs `null-install --answers`, and reboots into the installed system.

Where the answers can be:

| `null.autoinstall=` | Meaning |
|---|---|
| `http://10.0.0.5/answers.conf` | fetched over HTTP(S), retried for a couple of minutes while the network comes up |
| `/dev/disk/by-label/NULLCFG` | a second USB stick (any filesystem) labelled `NULLCFG` with `answers.conf` in its root |
| `/some/path` | a file already on the live system |

## answers.conf

```sh
NULL_DISK=/dev/sda              # erased
NULL_HOSTNAME=grid
NULL_USER=luc
NULL_PASSWORD='change me'
NULL_SSH_KEY='ssh-ed25519 AAAA... luc@laptop'   # optional; turns off SSH passwords
NULL_ROLES=nulldrive,containers # optional, comma-separated (null-extras list)
NULL_FS=ext4                    # ext4 (default), xfs or btrfs
NULL_TIMEZONE=Europe/Vilnius    # optional
NULL_REBOOT=1                   # 0 to stay in the live session afterwards
```

It's sourced by the shell, so quote values with spaces. The log is in `/var/log/null-install.log` (copied to `/tmp/null-install.log` in the live session).

## From the live session by hand

The same keys work as flags:

```
sudo null-install --disk /dev/sda --hostname grid --user luc --password '…' \
     --ssh-key-file ~/laptop.pub --roles nulldrive --yes
```
