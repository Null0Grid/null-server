#!/usr/bin/env python3
"""Boot a Null Server ISO in QEMU, screenshot the console, install it to a
virtual disk, reboot into the install and check it over SSH.

Usage: vm-test.py <iso> <out-dir>
Needs: qemu-system-x86_64 (or qemu-system-aarch64 + qemu-efi-aarch64 for an
arm64 ISO), python3-pil, sshpass. Uses KVM when /dev/kvm is usable.

Shots:
  01-boot-menu        ISO boot menu
  02-live-login       live session logged in on tty1 (MOTD, the prompt)
  03-null-info        null-info
  04-fastfetch        fastfetch with the Null mark logo
  05-root             root prompt (red frame)
  06-extras-list      null-extras list
  07-firewall         null-fw status, then null-fw allow 443
  08-install          null-install running (unattended flags)
  09-installed-login  first boot from disk: login prompt
  10-installed-motd   logged in: dynamic MOTD + prompt
  11-serial.txt       what the serial console printed during the boot
  12-ssh.txt          fastfetch, null-info, null-drive status over SSH
"""
import os
import socket
import subprocess
import sys
import time

from PIL import Image

ISO, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
MON = "/tmp/null-qemu-monitor.sock"
DISK = "/tmp/null-test-disk.qcow2"
SERIAL = os.path.join(OUT, "11-serial.txt")
KVM = os.access("/dev/kvm", os.R_OK | os.W_OK)
ARM = os.environ.get("NULL_VM_ARCH") == "arm64" or "arm64" in os.path.basename(ISO)
SLOW = 1 if KVM else (6 if ARM else 4)
SSH_PORT = 2222

KEYS = {" ": "spc", "-": "minus", "/": "slash", ".": "dot", "\n": "ret",
        "_": "shift-minus", "~": "shift-grave_accent", "|": "shift-backslash",
        "=": "equal", ":": "shift-semicolon", ">": "shift-dot",
        ";": "semicolon", "*": "shift-8", "'": "apostrophe", ",": "comma",
        "^": "shift-6", "$": "shift-4", "!": "shift-1", "#": "shift-3",
        "&": "shift-7", "\\": "backslash", "\"": "shift-apostrophe",
        "(": "shift-9", ")": "shift-0", "[": "bracket_left", "]": "bracket_right",
        "?": "shift-slash", "<": "shift-comma", "{": "shift-bracket_left", "}": "shift-bracket_right",
        "@": "shift-2", "%": "shift-5"}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def monitor(cmd):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        s.connect(MON)
        try:
            s.recv(4096)
        except socket.timeout:
            pass
        s.sendall((cmd + "\n").encode())
        time.sleep(0.15)
        try:
            s.recv(4096)
        except socket.timeout:
            log(f"monitor timeout on: {cmd}")


def key(name):
    monitor(f"sendkey {name}")
    time.sleep(0.08)


def type_text(text):
    for ch in text:
        if ch in KEYS:
            key(KEYS[ch])
        elif ch.isupper():
            key("shift-" + ch.lower())
        else:
            key(ch)


def shot(name):
    ppm = f"/tmp/{name}.ppm"
    try:
        monitor(f"screendump {ppm}")
        time.sleep(1)
        Image.open(ppm).save(os.path.join(OUT, f"{name}.png"))
        log(f"saved {name}.png")
    except Exception as e:
        log(f"could not take {name}: {e}")


def wait(seconds, why):
    log(f"waiting {seconds * SLOW}s: {why}")
    time.sleep(seconds * SLOW)


def serial_has(text, timeout):
    """Wait until the serial log contains text (the console is mirrored there)."""
    end = time.time() + timeout * SLOW
    while time.time() < end:
        try:
            if text in open(SERIAL, errors="replace").read():
                return True
        except FileNotFoundError:
            pass
        time.sleep(2)
    log(f"serial: '{text}' not seen within {timeout * SLOW}s")
    return False


def qemu_cmd(boot_iso):
    common = ["-m", "2048", "-display", "none",
              "-monitor", f"unix:{MON},server,nowait",
              "-serial", f"file:{SERIAL}",
              "-nic", f"user,model=virtio-net-pci,hostfwd=tcp::{SSH_PORT}-:22",
              "-drive", f"file={DISK},if=virtio,format=qcow2"]
    if ARM:
        fw = next((f for f in ("/usr/share/qemu-efi-aarch64/QEMU_EFI.fd", "/usr/share/AAVMF/AAVMF_CODE.fd")
                   if os.path.exists(f)), None)
        cmd = ["qemu-system-aarch64", "-M", "virt", "-smp", str(min(os.cpu_count() or 2, 4)), "-bios", fw,
               "-device", "virtio-gpu-pci", "-device", "qemu-xhci", "-device", "usb-kbd"] + common
        if boot_iso:
            cmd += ["-device", "virtio-scsi-pci", "-drive", f"file={ISO},if=none,id=cd,media=cdrom,readonly=on",
                    "-device", "scsi-cd,drive=cd,bootindex=0"]
        cmd += ["-enable-kvm", "-cpu", "host"] if KVM else ["-cpu", "max", "-accel", "tcg,thread=multi"]
    else:
        cmd = ["qemu-system-x86_64", "-smp", "2", "-vga", "std"] + common
        if boot_iso:
            cmd += ["-cdrom", ISO, "-boot", "once=d"]
        if KVM:
            cmd += ["-enable-kvm", "-cpu", "host"]
    return cmd


def start(boot_iso):
    if os.path.exists(MON):
        os.remove(MON)
    vm = subprocess.Popen(qemu_cmd(boot_iso))
    for _ in range(50):
        if os.path.exists(MON):
            break
        time.sleep(0.2)
    return vm


def ssh(cmd, timeout=120):
    r = subprocess.run(["sshpass", "-p", "live", "ssh", "-p", str(SSH_PORT), "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=10", "-o", "LogLevel=ERROR",
                        "luc@127.0.0.1", cmd], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def main():
    subprocess.run(["qemu-img", "create", "-f", "qcow2", DISK, "8G"], check=True, stdout=subprocess.DEVNULL)
    if os.path.exists(SERIAL):
        os.remove(SERIAL)

    # ---- Live ISO ----
    vm = start(boot_iso=True)
    try:
        wait(8, "boot menu")
        shot("01-boot-menu")
        key("ret")
        serial_has("login:", 180) or serial_has("user", 60)
        wait(15, "autologin on tty1")
        shot("02-live-login")
        type_text("clear; null-info\n")
        wait(6, "null-info")
        shot("03-null-info")
        type_text("clear; fastfetch\n")
        wait(8, "fastfetch")
        shot("04-fastfetch")
        type_text("clear; sudo -i\n")
        wait(4, "root shell")
        type_text("ls /etc; false\n")
        wait(3, "root prompt with an error code")
        shot("05-root")
        type_text("exit\n")
        type_text("clear; null-extras list\n")
        wait(6, "extras list")
        shot("06-extras-list")
        type_text("clear; null-fw status; sudo null-fw allow 443; sudo nft list set inet null tcp_open\n")
        wait(8, "firewall")
        shot("07-firewall")
        type_text("clear; sudo null-install --disk /dev/vda --hostname grid --user luc --password live --roles '' --yes 2>&1 | tail -40\n")
        wait(20, "install starts")
        shot("08-install")
        serial_has("Null Server is on /dev/vda", 900)
        wait(5, "install done")
        shot("08b-install-done")
        type_text("sudo poweroff\n")
        vm.wait(timeout=120 * SLOW)
    finally:
        if vm.poll() is None:
            vm.kill()

    # ---- Installed system ----
    vm = start(boot_iso=False)
    try:
        ok = serial_has("grid login:", 240)
        wait(10, "first boot from disk")
        shot("09-installed-login")
        type_text("luc\n")
        wait(3, "password prompt")
        type_text("live\n")
        wait(8, "login + MOTD")
        shot("10-installed-motd")
        type_text("fastfetch\n")
        wait(8, "fastfetch on the installed system")
        shot("10b-installed-fastfetch")
        # SSH: the real check that the install works
        out = []
        for attempt in range(12):
            rc, txt = ssh("echo SSH-OK")
            if rc == 0 and "SSH-OK" in txt:
                break
            time.sleep(10)
        for c in ("fastfetch --pipe false", "null-info", "null-drive status", "null-fw status",
                  "systemctl --failed --no-pager", "cat /etc/os-release", "echo $SHELL; zsh -ic 'print -P \"$PROMPT\"'"):
            rc, txt = ssh(c)
            out.append(f"$ {c}\n{txt}\n")
        with open(os.path.join(OUT, "12-ssh.txt"), "w") as f:
            f.write("".join(out))
        log("ssh checks written" if ok else "installed system never showed a login prompt")
        ssh("echo live | sudo -S poweroff")
        vm.wait(timeout=120 * SLOW)
    finally:
        if vm.poll() is None:
            vm.kill()


if __name__ == "__main__":
    main()
