#!/bin/bash
# Build the Null Server ISO. Run as root on Debian 12/13 (or via docker-build.sh).
set -euo pipefail
cd "$(dirname "$0")"
. ./null-server.conf
export ARCH

[ "$(id -u)" -eq 0 ] || { echo "Run as root (sudo ./build.sh)"; exit 1; }
grep -qi debian /etc/os-release || echo "WARNING: not a Debian host; use ./docker-build.sh if this fails."

echo ">> Installing build tools"
apt-get update -qq
case "$ARCH" in
  arm64) BOOT_TOOLS="grub-efi-arm64-bin" ;;
  *)     BOOT_TOOLS="isolinux syslinux-common grub-efi-amd64-bin grub-pc-bin" ;;
esac
# shellcheck disable=SC2086
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  live-build debootstrap squashfs-tools xorriso $BOOT_TOOLS mtools dosfstools ca-certificates \
  curl git jq python3 >/dev/null

echo ">> Writing release info from null-server.conf"
cat > config/includes.chroot/etc/null-server-release <<REL
NULL_NAME="$DISTRO_NAME"
NULL_ID="$DISTRO_ID"
NULL_VERSION="$DISTRO_VERSION"
NULL_ARCH="$ARCH"
REL

echo ">> Cleaning previous build"
lb clean --purge >/dev/null 2>&1 || true

echo ">> Configuring ($DEBIAN_SUITE/$ARCH)"
lb config

echo ">> Null Server boot menu (replaces the Debian splash)"
mkdir -p config/bootloaders
for src in /usr/share/live/build/bootloaders/*/; do
  d=$(basename "$src")
  rm -rf "config/bootloaders/$d"
  cp -a "$src" "config/bootloaders/$d"
done
cp branding/boot-splash.svg config/bootloaders/splash.svg
cp branding/boot-splash.svg config/bootloaders/splash.svg.in
cp branding/boot-splash.png config/bootloaders/splash.png
find config/bootloaders -iname 'splash*.svg*' -exec cp branding/boot-splash.svg {} \;
find config/bootloaders -iname 'splash*.png'  -exec cp branding/boot-splash.png {} \;
# Menu highlight in Null cyan
find config/bootloaders -name 'stdmenu.cfg' -exec sed -i \
  -e 's/#76a1d0ff/#ff00e5ff/g' -e 's/^\(menu color sel \* \)#ffffffff/\1#ff0a0a0f/' {} \;

echo ">> Building (20-40 min depending on mirror speed)"
lb build

ISO_OUT="${DISTRO_ID}-${DISTRO_VERSION}-${DEBIAN_SUITE}-${ARCH}.iso"
mv -f live-image-*.hybrid.iso "$ISO_OUT"
sha256sum "$ISO_OUT" > "$ISO_OUT.sha256"
echo ">> Done: $(pwd)/$ISO_OUT ($(du -h "$ISO_OUT" | cut -f1))"
