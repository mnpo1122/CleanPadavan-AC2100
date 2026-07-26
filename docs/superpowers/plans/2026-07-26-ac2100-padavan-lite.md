# AC2100 Padavan 4.4 Lite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a GitHub Actions builder that clones MeIsReallyBa/padavan-4.4, overlays a pure-router RM2100 config + 1000 MHz OC kernel fragment, and publishes a flashable `.trx`.

**Architecture:** In-repo config overlay (Approach B). CI checks out this repo, clones upstream Padavan shallow, copies `configs/RM2100.config` over the board template, merges `configs/kernel-oc.fragment` into the board kernel config, builds `RM2100`, uploads Release. A small Python self-check validates the overlay before CI/local use.

**Tech Stack:** GitHub Actions (`ubuntu-22.04`), Padavan 4.4 (`MeIsReallyBa/padavan-4.4`), mipsel toolchain script, Python 3 stdlib for config checks, softprops/action-gh-release.

**Spec:** `CleanPadavan-AC2100-main/DESIGN.md` (and `docs/superpowers/specs/2026-07-26-ac2100-padavan-lite-design.md`)

---

## File map

| Path | Role |
|------|------|
| `configs/RM2100.config` | Userspace firmware template (source of truth) |
| `configs/kernel-oc.fragment` | `CONFIG_MT7621_OC` + MPLL hex |
| `scripts/check_lite_config.py` | Assert lite invariants (run in CI + local) |
| `.github/workflows/build-padavan.yml` | Single build/release workflow |
| `.github/workflows/build-Gemini.yml` | **Delete** after new workflow works |
| `README.md` | Usage, defaults, OC/Breed warnings |
| `DESIGN.md` | Already committed — do not rewrite unless spec changes |

Working directory for all paths below: `CleanPadavan-AC2100-main/` (repo root may be parent `windowrunner`; keep paths relative to the CleanPadavan project).

---

### Task 1: Kernel OC fragment

**Files:**
- Create: `CleanPadavan-AC2100-main/configs/kernel-oc.fragment`
- Test: `CleanPadavan-AC2100-main/scripts/check_lite_config.py` (added Task 3; fragment checked there)

- [ ] **Step 1: Create configs directory and fragment**

```bash
mkdir -p CleanPadavan-AC2100-main/configs
```

Write `CleanPadavan-AC2100-main/configs/kernel-oc.fragment` exactly:

```
# MT7621 mild OC ~1000MHz (MPLL hex for CONFIG_MT7621_CPU_FREQ)
# Applied into configs/boards/RM2100/kernel-4.4.x.config at build time.
# Verify on device: dmesg | grep "CPU Clock"
CONFIG_MT7621_OC=y
CONFIG_MT7621_CPU_FREQ="0x312"
```

- [ ] **Step 2: Sanity-read file**

Run:

```bash
cat CleanPadavan-AC2100-main/configs/kernel-oc.fragment
```

Expected: two `CONFIG_MT7621_*` lines present; `0x312` quoted.

- [ ] **Step 3: Commit**

```bash
git add CleanPadavan-AC2100-main/configs/kernel-oc.fragment
git commit -m "feat(ac2100): add MT7621 OC 1000MHz kernel fragment"
```

---

### Task 2: Lite RM2100 userspace config overlay

**Files:**
- Create: `CleanPadavan-AC2100-main/configs/RM2100.config`
- Reference base: upstream MeIsReallyBa `trunk/configs/templates/RM2100.config` (fetch if missing)

- [ ] **Step 1: Write lite template**

Create `CleanPadavan-AC2100-main/configs/RM2100.config` with this full content (upstream base + lite cuts):

```
### Target Vendor/Product (support only Ralink RT3883/MT7620/MT7621/MT7628)
CONFIG_VENDOR=Ralink
CONFIG_PRODUCT=MT7621

### Target ProductID (board select, max 12 symbols)
CONFIG_FIRMWARE_PRODUCT_ID="RM2100"

### Linux kernel and toolchain
### SFE = shortcut-forwarding / HW NAT path for MT7621
CONFIG_FIRMWARE_INCLUDE_SFE=y

CONFIG_LINUXDIR=linux-4.4.x

############################################################
### Linux kernel configuration
############################################################

### Enable IPv6 support
CONFIG_FIRMWARE_ENABLE_IPV6=y

### Enable USB support
CONFIG_FIRMWARE_ENABLE_USB=n

### Enable FAT/FAT32 filesystem support. ~0.1MB
CONFIG_FIRMWARE_ENABLE_FAT=n

### Enable exFAT (FAT/FAT32 too) filesystem support. ~0.12MB
CONFIG_FIRMWARE_ENABLE_EXFAT=n

### Enable EXT2 filesystem support. ~0.1MB
CONFIG_FIRMWARE_ENABLE_EXT2=n

### Enable EXT3 filesystem support. ~0.2MB
CONFIG_FIRMWARE_ENABLE_EXT3=n

### Enable EXT4 (EXT3/2 too) filesystem support. ~0.4MB
CONFIG_FIRMWARE_ENABLE_EXT4=n

### Enable XFS filesystem support. ~0.6MB
CONFIG_FIRMWARE_ENABLE_XFS=n

### Enable FUSE (filesystems in userspace) support. ~0.1MB
CONFIG_FIRMWARE_ENABLE_FUSE=n

### Enable swap files/partitions support. ~0.05MB
CONFIG_FIRMWARE_ENABLE_SWAP=n

### Include UVC camera modules. ~0.2MB
CONFIG_FIRMWARE_INCLUDE_UVC=n

### Include USB-HID modules. ~0.2MB
CONFIG_FIRMWARE_INCLUDE_HID=n

### Include USB-Serial modules (e.g. pl2303). ~0.03MB
CONFIG_FIRMWARE_INCLUDE_SERIAL=n

### Include USB-Audio modules ~0.46MB
CONFIG_FIRMWARE_INCLUDE_AUDIO=n

### Include XFRM (IPsec) modules & iptables extension ~ 0.2MB
CONFIG_FIRMWARE_INCLUDE_XFRM=n

### Include network QoS scheduling modules. ~0.2MB
CONFIG_FIRMWARE_INCLUDE_QOS=n

### Include IMQ module for shapers (a bit of performance degradation). ~0.02MB
CONFIG_FIRMWARE_INCLUDE_IMQ=n

### Include IFB module for shapers. ~0.03MB
CONFIG_FIRMWARE_INCLUDE_IFB=n

### Include IPSet utility and kernel modules. ~0.4MB
CONFIG_FIRMWARE_INCLUDE_IPSET=n

### Include NFSv3 server. ~0.6MB
CONFIG_FIRMWARE_INCLUDE_NFSD=n

### Include NFSv3 client. ~0.5MB
CONFIG_FIRMWARE_INCLUDE_NFSC=n

### Include CIFS (SMB) client. ~0.2MB
CONFIG_FIRMWARE_INCLUDE_CIFS=n

############################################################
### Userspace configuration
############################################################

### Include WebUI international resources. Increased firmware size
CONFIG_FIRMWARE_INCLUDE_LANG_CN=y
#CONFIG_FIRMWARE_INCLUDE_LANG_BR=y
#CONFIG_FIRMWARE_INCLUDE_LANG_CZ=y
#CONFIG_FIRMWARE_INCLUDE_LANG_DA=y
#CONFIG_FIRMWARE_INCLUDE_LANG_DE=y
#CONFIG_FIRMWARE_INCLUDE_LANG_ES=y
#CONFIG_FIRMWARE_INCLUDE_LANG_FI=y
#CONFIG_FIRMWARE_INCLUDE_LANG_FR=y
#CONFIG_FIRMWARE_INCLUDE_LANG_NO=y
#CONFIG_FIRMWARE_INCLUDE_LANG_PL=y
#CONFIG_FIRMWARE_INCLUDE_LANG_RU=y
#CONFIG_FIRMWARE_INCLUDE_LANG_SV=y
#CONFIG_FIRMWARE_INCLUDE_LANG_UK=y

### Include NTFS-3G FUSE driver (instead of Paragon "ufsd"). ~0.4MB
CONFIG_FIRMWARE_INCLUDE_NTFS_3G=n

### Include LPR printer daemon. ~0.12MB
CONFIG_FIRMWARE_INCLUDE_LPRD=n

### Include USB-over-Ethernet printer daemon. ~0.05MB
CONFIG_FIRMWARE_INCLUDE_U2EC=n

### Include "tcpdump" utility. ~0.6MB
CONFIG_FIRMWARE_INCLUDE_TCPDUMP=n

### Include "hdparm" utility (allow set HDD spindown timeout and APM). ~0.1MB
CONFIG_FIRMWARE_INCLUDE_HDPARM=n

### Include "parted" utility (allow make GPT partitions). ~0.3MB
CONFIG_FIRMWARE_INCLUDE_PARTED=n

### Include SMB3.6 (and WINS) server. ~1.5MB
CONFIG_FIRMWARE_INCLUDE_SMBD=n

### Include WINS server only. ~0.4MB
CONFIG_FIRMWARE_INCLUDE_WINS=n

### Include syslog for SMB and WINS server. ~0.3MB
CONFIG_FIRMWARE_INCLUDE_SMBD_SYSLOG=n

### Include FTP server. ~0.2MB
CONFIG_FIRMWARE_INCLUDE_FTPD=n

### Include alternative L2TP control client RP-L2TP. ~0.1MB
CONFIG_FIRMWARE_INCLUDE_RPL2TP=n

### Include EAP-TTLS and EAP-PEAP authentication support. openssl ~1.2MB, wpa_supplicant +0.04MB
CONFIG_FIRMWARE_INCLUDE_EAP_PEAP=n

### Include HTTPS support. openssl ~1.2MB
CONFIG_FIRMWARE_INCLUDE_HTTPS=n

### Include sftp-server. openssl ~1.2MB, sftp-server ~0.06MB
CONFIG_FIRMWARE_INCLUDE_SFTP=n

### Include dropbear SSH. ~0.3MB
CONFIG_FIRMWARE_INCLUDE_DROPBEAR=n

### Make the dropbear symmetrical ciphers and hashes faster. ~0.06MB
CONFIG_FIRMWARE_INCLUDE_DROPBEAR_FAST_CODE=n

### Include OpenSSH instead of dropbear. openssl ~1.2MB, openssh ~1.0MB
CONFIG_FIRMWARE_INCLUDE_OPENSSH=n

### Include OpenVPN. IPv6 required. openssl ~1.2MB, openvpn ~0.4MB
CONFIG_FIRMWARE_INCLUDE_OPENVPN=n

### Include StrongSwan. XFRM modules ~0.2MB, strongswan ~0.7MB
CONFIG_FIRMWARE_INCLUDE_SSWAN=n

### Include Elliptic Curves (EC) to openssl library. ~0.1MB
CONFIG_FIRMWARE_INCLUDE_OPENSSL_EC=n

### Include "openssl" executable for generate certificates. ~0.4MB
CONFIG_FIRMWARE_INCLUDE_OPENSSL_EXE=n

### Include xUPNPd IPTV mediaserver. ~0.3MB
CONFIG_FIRMWARE_INCLUDE_XUPNPD=n

### Include Minidlna UPnP mediaserver. ~1.6MB
CONFIG_FIRMWARE_INCLUDE_MINIDLNA=n

### Include Firefly iTunes mediaserver. ~1.0MB
CONFIG_FIRMWARE_INCLUDE_FIREFLY=n

### Include ffmpeg 0.11.x instead of 0.6.x for Minidlna and Firefly. ~0.1MB
CONFIG_FIRMWARE_INCLUDE_FFMPEG_NEW=n

### Include Transmission torrent. openssl ~1.2MB, transmission ~1.5MB
CONFIG_FIRMWARE_INCLUDE_TRANSMISSION=n

### Include Transmission-Web-Control (advanced WebUI). ~0.8MB
CONFIG_FIRMWARE_INCLUDE_TRANSMISSION_WEB_CONTROL=n

### Include Aria2 download manager. openssl ~1.2MB, aria2 ~3.5MB
CONFIG_FIRMWARE_INCLUDE_ARIA=n

### Include Aria2 WEB control. ~0.7MB
CONFIG_FIRMWARE_INCLUDE_ARIA_WEB_CONTROL=n

CONFIG_FIRMWARE_INCLUDE_CURL=n

CONFIG_FIRMWARE_INCLUDE_SCUTCLIENT=n

CONFIG_FIRMWARE_INCLUDE_GDUT_DRCOM=n

CONFIG_FIRMWARE_INCLUDE_DOGCOM=n

CONFIG_FIRMWARE_INCLUDE_MINIEAP=n

CONFIG_FIRMWARE_INCLUDE_NJIT_CLIENT=n

CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_SERVER=n

CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_CLIENT=n

CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_CMD=n

CONFIG_FIRMWARE_INCLUDE_VLMCSD=n

CONFIG_FIRMWARE_INCLUDE_TTYD=n

CONFIG_FIRMWARE_INCLUDE_LRZSZ=n

CONFIG_FIRMWARE_INCLUDE_HTOP=n

CONFIG_FIRMWARE_INCLUDE_NANO=n

CONFIG_FIRMWARE_INCLUDE_IPERF3=n

CONFIG_FIRMWARE_INCLUDE_DUMP1090=n

CONFIG_FIRMWARE_INCLUDE_RTL_SDR=n

CONFIG_FIRMWARE_INCLUDE_MTR=n

CONFIG_FIRMWARE_INCLUDE_SOCAT=n

CONFIG_FIRMWARE_INCLUDE_SRELAY=n

CONFIG_FIRMWARE_INCLUDE_MENTOHUST=n

CONFIG_FIRMWARE_INCLUDE_FRPC=n

CONFIG_FIRMWARE_INCLUDE_FRPS=n

CONFIG_FIRMWARE_INCLUDE_WIREGUARD=n
```

Lite deltas vs upstream (must be `n`):  
`IPSET`, `EAP_PEAP`, `SFTP`, `OPENSSH`, `OPENSSL_EC`, `OPENSSL_EXE`, `FFMPEG_NEW`, `CURL`, `VLMCSD`, `HTOP`, `IPERF3`, `MTR`, `SOCAT`.

Keep `y`: `SFE`, `IPV6`, `LANG_CN`.

- [ ] **Step 2: Spot-check critical keys**

Run:

```bash
rg "CONFIG_FIRMWARE_INCLUDE_(SFE|OPENSSH|DROPBEAR|SFTP|ARIA|SFE)|CONFIG_FIRMWARE_ENABLE_IPV6|CONFIG_FIRMWARE_INCLUDE_SFE" CleanPadavan-AC2100-main/configs/RM2100.config
```

Expected:
- `SFE=y`, `IPV6=y`
- `OPENSSH=n`, `DROPBEAR=n`, `SFTP=n`, `ARIA=n`

- [ ] **Step 3: Commit**

```bash
git add CleanPadavan-AC2100-main/configs/RM2100.config
git commit -m "feat(ac2100): add pure-router RM2100.config overlay"
```

---

### Task 3: Config self-check script

**Files:**
- Create: `CleanPadavan-AC2100-main/scripts/check_lite_config.py`

- [ ] **Step 1: Write checker**

```python
#!/usr/bin/env python3
"""Assert Padavan lite overlay invariants. Exit 0 ok, 1 fail."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs" / "RM2100.config"
OC = ROOT / "configs" / "kernel-oc.fragment"

MUST_Y = [
    "CONFIG_FIRMWARE_INCLUDE_SFE",
    "CONFIG_FIRMWARE_ENABLE_IPV6",
    "CONFIG_FIRMWARE_INCLUDE_LANG_CN",
]

MUST_N = [
    "CONFIG_FIRMWARE_INCLUDE_OPENSSH",
    "CONFIG_FIRMWARE_INCLUDE_DROPBEAR",
    "CONFIG_FIRMWARE_INCLUDE_SFTP",
    "CONFIG_FIRMWARE_INCLUDE_ARIA",
    "CONFIG_FIRMWARE_INCLUDE_TRANSMISSION",
    "CONFIG_FIRMWARE_INCLUDE_OPENVPN",
    "CONFIG_FIRMWARE_INCLUDE_WIREGUARD",
    "CONFIG_FIRMWARE_INCLUDE_CURL",
    "CONFIG_FIRMWARE_INCLUDE_HTOP",
    "CONFIG_FIRMWARE_INCLUDE_IPERF3",
    "CONFIG_FIRMWARE_INCLUDE_VLMCSD",
    "CONFIG_FIRMWARE_INCLUDE_IPSET",
    "CONFIG_FIRMWARE_ENABLE_USB",
]

KV = re.compile(r"^(CONFIG_[A-Z0-9_]+)=(.*)$")


def load_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = KV.match(s)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def main() -> int:
    errors: list[str] = []
    if not CFG.is_file():
        print(f"FAIL missing {CFG}")
        return 1
    if not OC.is_file():
        print(f"FAIL missing {OC}")
        return 1

    cfg = load_kv(CFG)
    if cfg.get("CONFIG_FIRMWARE_PRODUCT_ID") != "RM2100":
        errors.append(f"PRODUCT_ID={cfg.get('CONFIG_FIRMWARE_PRODUCT_ID')!r} want RM2100")
    if cfg.get("CONFIG_LINUXDIR") != "linux-4.4.x":
        errors.append(f"LINUXDIR={cfg.get('CONFIG_LINUXDIR')!r} want linux-4.4.x")

    for k in MUST_Y:
        if cfg.get(k) != "y":
            errors.append(f"{k} want y got {cfg.get(k)!r}")
    for k in MUST_N:
        if cfg.get(k) != "n":
            errors.append(f"{k} want n got {cfg.get(k)!r}")

    oc = load_kv(OC)
    if oc.get("CONFIG_MT7621_OC") != "y":
        errors.append("CONFIG_MT7621_OC want y")
    if oc.get("CONFIG_MT7621_CPU_FREQ") != "0x312":
        errors.append(
            f"CONFIG_MT7621_CPU_FREQ want 0x312 got {oc.get('CONFIG_MT7621_CPU_FREQ')!r}"
        )

    if errors:
        print("FAIL lite config check:")
        for e in errors:
            print(" -", e)
        return 1
    print("OK lite config check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run checker (expect PASS after Task 1–2)**

```bash
python CleanPadavan-AC2100-main/scripts/check_lite_config.py
```

Expected stdout: `OK lite config check`  
Exit code: `0`

- [ ] **Step 3: Negative check (optional local)**

Temporarily flip `CONFIG_FIRMWARE_INCLUDE_OPENSSH=y` in RM2100.config, re-run checker → must exit `1` and mention OPENSSH. Revert to `n`.

- [ ] **Step 4: Commit**

```bash
git add CleanPadavan-AC2100-main/scripts/check_lite_config.py
git commit -m "test(ac2100): add lite config invariant checker"
```

---

### Task 4: GitHub Actions workflow

**Files:**
- Create: `CleanPadavan-AC2100-main/.github/workflows/build-padavan.yml`
- Delete (Task 5): `CleanPadavan-AC2100-main/.github/workflows/build-Gemini.yml`

- [ ] **Step 1: Write workflow**

Create `CleanPadavan-AC2100-main/.github/workflows/build-padavan.yml`:

```yaml
name: Build Redmi AC2100 Padavan Lite

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  check:
    runs-on: ubuntu-22.04
    steps:
      - name: Checkout overlays
        uses: actions/checkout@v4

      - name: Validate lite config
        run: python3 scripts/check_lite_config.py

  build:
    needs: check
    runs-on: ubuntu-22.04
    steps:
      - name: Checkout overlays
        uses: actions/checkout@v4

      - name: Prepare Environment
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libtool-bin curl cmake gperf gawk flex bison \
            nano xxd fakeroot kmod cpio git-doc vim-common \
            libncurses5-dev libncurses5 \
            python3-docutils autopoint texinfo
          sudo apt-get clean

      - name: Build firmware
        run: |
          set -euo pipefail
          WORK_DIR="${GITHUB_WORKSPACE}/padavan"
          OVERLAY_CFG="${GITHUB_WORKSPACE}/configs/RM2100.config"
          OVERLAY_OC="${GITHUB_WORKSPACE}/configs/kernel-oc.fragment"
          TARGET_DEVICE="RM2100"
          CURRENT_DATE="$(date +%Y%m%d)"
          echo "DATE=${CURRENT_DATE}" >> "${GITHUB_ENV}"
          echo "BUILD_VER=4.4-oc1000-lite" >> "${GITHUB_ENV}"

          echo "Cloning MeIsReallyBa/padavan-4.4..."
          git clone --depth=1 --branch main \
            https://github.com/MeIsReallyBa/padavan-4.4.git \
            "${WORK_DIR}"

          echo "Preparing toolchain..."
          cd "${WORK_DIR}/toolchain-mipsel"
          sh dl_toolchain.sh

          TEMPLATE_PATH="${WORK_DIR}/trunk/configs/templates/${TARGET_DEVICE}.config"
          KERNEL_CFG="${WORK_DIR}/trunk/configs/boards/${TARGET_DEVICE}/kernel-4.4.x.config"

          test -f "${TEMPLATE_PATH}" || { echo "missing template ${TEMPLATE_PATH}"; exit 1; }
          test -f "${KERNEL_CFG}" || { echo "missing kernel cfg ${KERNEL_CFG}"; exit 1; }
          test -f "${OVERLAY_CFG}" || { echo "missing overlay ${OVERLAY_CFG}"; exit 1; }
          test -f "${OVERLAY_OC}" || { echo "missing OC fragment ${OVERLAY_OC}"; exit 1; }

          echo "Applying userspace overlay..."
          cp -f "${OVERLAY_CFG}" "${TEMPLATE_PATH}"

          echo "Merging kernel OC fragment..."
          # drop prior OC keys then append fragment
          sed -i \
            -e '/^CONFIG_MT7621_OC=/d' \
            -e '/^# CONFIG_MT7621_OC is not set/d' \
            -e '/^CONFIG_MT7621_CPU_FREQ=/d' \
            "${KERNEL_CFG}"
          cat "${OVERLAY_OC}" >> "${KERNEL_CFG}"
          grep -E 'CONFIG_MT7621_OC|CONFIG_MT7621_CPU_FREQ' "${KERNEL_CFG}"

          # optional: Flow Offload symbol if tree defines it in template schema
          if grep -q 'CONFIG_FIRMWARE_ENABLE_FLOWOFFLOAD' "${TEMPLATE_PATH}" 2>/dev/null; then
            sed -i 's/CONFIG_FIRMWARE_ENABLE_FLOWOFFLOAD=n/CONFIG_FIRMWARE_ENABLE_FLOWOFFLOAD=y/g' "${TEMPLATE_PATH}"
          fi

          cd "${WORK_DIR}/trunk"
          cp -f "${TEMPLATE_PATH}" .config
          test -f .config

          echo "Starting build for ${TARGET_DEVICE}..."
          fakeroot ./build_firmware "${TARGET_DEVICE}"

          ls -la images/ || true
          test -n "$(ls images/*.trx 2>/dev/null)" || { echo "no trx produced"; exit 1; }

      - name: Organize Artifacts
        run: |
          mkdir -p ./output_firmware
          cp "${GITHUB_WORKSPACE}/padavan/trunk/images/"*.trx ./output_firmware/
          ls -la ./output_firmware
          echo "FIRMWARE_PATH=./output_firmware" >> "${GITHUB_ENV}"

      - name: Upload firmware artifact
        uses: actions/upload-artifact@v4
        with:
          name: RM2100-padavan-4.4-oc1000-lite-${{ env.DATE }}
          path: ${{ env.FIRMWARE_PATH }}/*.trx
          if-no-files-found: error

      - name: Upload Firmware to Releases
        uses: softprops/action-gh-release@v2
        if: success()
        with:
          tag_name: v${{ env.DATE }}-${{ env.BUILD_VER }}
          name: Redmi AC2100 Padavan ${{ env.BUILD_VER }} (${{ env.DATE }})
          body: |
            Auto-built lite firmware

            - Device: Redmi AC2100 (RM2100)
            - Tree: MeIsReallyBa/padavan-4.4 (linux-4.4.x)
            - CPU: OC ~1000 MHz (`CONFIG_MT7621_OC`, MPLL `0x312`)
            - Accel: SFE enabled
            - Features: pure router + IPv6
            - Removed: SSH, USB, downloaders, VPN/proxy plugins, debug tools
            - Flash via Breed; OC may be unstable — keep a recovery image
          files: ${{ env.FIRMWARE_PATH }}/*.trx
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: YAML lint (local if available)**

```bash
python -c "import yaml,sys; yaml.safe_load(open('CleanPadavan-AC2100-main/.github/workflows/build-padavan.yml')); print('yaml ok')"
```

If PyYAML missing, skip — Actions will validate on push.

- [ ] **Step 3: Commit**

```bash
git add CleanPadavan-AC2100-main/.github/workflows/build-padavan.yml
git commit -m "feat(ac2100): add padavan-4.4 lite build workflow"
```

---

### Task 5: Remove legacy dual-version workflow

**Files:**
- Delete: `CleanPadavan-AC2100-main/.github/workflows/build-Gemini.yml`

- [ ] **Step 1: Delete file**

```bash
git rm CleanPadavan-AC2100-main/.github/workflows/build-Gemini.yml
```

- [ ] **Step 2: Confirm only one workflow**

```bash
ls CleanPadavan-AC2100-main/.github/workflows/
```

Expected: only `build-padavan.yml`

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(ac2100): drop legacy Gemini dual-version workflow"
```

---

### Task 6: README rewrite

**Files:**
- Modify: `CleanPadavan-AC2100-main/README.md`

- [ ] **Step 1: Replace README content**

```markdown
# Redmi AC2100 Padavan Lite Builder

GitHub Actions builder for **Redmi AC2100 (RM2100)** Padavan firmware.

- Source: [MeIsReallyBa/padavan-4.4](https://github.com/MeIsReallyBa/padavan-4.4) (`linux-4.4.x`)
- Profile: pure router + IPv6, **no plugins**, **no SSH**
- Accel: **SFE** on
- CPU: mild OC **~1000 MHz** (`CONFIG_MT7621_OC`, MPLL `0x312`)

## Build

1. Fork this repo.
2. Actions → **Build Redmi AC2100 Padavan Lite** → **Run workflow**.
3. Wait for compile; download `.trx` from **Artifacts** or **Releases**.

Local config check (no full build):

```bash
python3 scripts/check_lite_config.py
```

## Defaults

| Item | Value |
|------|--------|
| LAN | `192.168.123.1` |
| User / pass | `admin` / `admin` |
| WiFi password | `1234567890` |

Change credentials after first login.

## Flash

Use **Breed**. Keep a known-good image. OC can brick unstable boards — recover via Breed.

After boot, optional check:

```text
dmesg | grep "CPU Clock"
```

Expect near **1000 MHz**. If not, edit `configs/kernel-oc.fragment` hex only.

## Customize

- Userspace features: edit `configs/RM2100.config` (`=y` / `=n`), re-run checker.
- OC: edit `configs/kernel-oc.fragment`.
- Do **not** put heavy services (RustDesk relay, downloaders, VPN) in this image; use a side device.

## Layout

```text
configs/RM2100.config          # firmware template overlay
configs/kernel-oc.fragment     # MT7621 OC
scripts/check_lite_config.py   # lite invariants
.github/workflows/build-padavan.yml
DESIGN.md                      # design spec
```

## Credits

- [MeIsReallyBa/padavan-4.4](https://github.com/MeIsReallyBa/padavan-4.4)
- [hanwckf/padavan-4.4](https://github.com/hanwckf/padavan-4.4) / [hanwckf/rt-n56u](https://github.com/hanwckf/rt-n56u)

## Disclaimer

Flashing is at your own risk. This repo only provides build scripts/overlays.
```

- [ ] **Step 2: Commit**

```bash
git add CleanPadavan-AC2100-main/README.md
git commit -m "docs(ac2100): README for 4.4 lite OC builder"
```

---

### Task 7: Cleanup temp files + final verify

**Files:**
- Delete if present: `CleanPadavan-AC2100-main/_upstream_RM2100.config`

- [ ] **Step 1: Remove scratch upstream dump**

```bash
rm -f CleanPadavan-AC2100-main/_upstream_RM2100.config
```

- [ ] **Step 2: Run checker**

```bash
python CleanPadavan-AC2100-main/scripts/check_lite_config.py
```

Expected: `OK lite config check`

- [ ] **Step 3: Tree check**

```bash
# from CleanPadavan-AC2100-main
find configs scripts .github/workflows -type f | sort
```

Expected files:

```
.github/workflows/build-padavan.yml
configs/RM2100.config
configs/kernel-oc.fragment
scripts/check_lite_config.py
```

No `build-Gemini.yml`.

- [ ] **Step 4: Commit any leftover cleanup**

```bash
git status
# if dirty:
git add -A CleanPadavan-AC2100-main
git commit -m "chore(ac2100): cleanup scratch files"
```

- [ ] **Step 5: (Human) Run Actions**

On GitHub: Run workflow once. Success = `.trx` artifact + Release tag `vYYYYMMDD-4.4-oc1000-lite`.  
Failure = open log; common fixes: apt dep, toolchain download, missing board file — fix workflow only, not re-expand scope.

---

## Self-review (plan vs DESIGN.md)

| Spec requirement | Task |
|------------------|------|
| MeIsReallyBa padavan-4.4 only | Task 4 clone URL |
| RM2100 | Task 2 PRODUCT_ID + Task 4 TARGET_DEVICE |
| OC 1000 / `0x312` | Task 1 + Task 4 merge |
| SFE on | Task 2 + Task 3 MUST_Y |
| IPv6 on | Task 2 + Task 3 |
| No SSH | Task 2 OPENSSH/DROPBEAR/SFTP=n + checker |
| Pure router, cut tools/plugins | Task 2 MUST_N list |
| Config overlay Approach B | Tasks 1–2 + Task 4 cp/merge |
| Release naming | Task 4 tag `vDATE-4.4-oc1000-lite` |
| README OC/Breed/no SSH | Task 6 |
| Drop dual 3.4 workflow | Task 5 |
| Flow Offload if symbol exists | Task 4 optional sed |
| No RustDesk / OpenWrt | not in plan (YAGNI) |

Placeholder scan: none.  
Types/names: `CONFIG_MT7621_CPU_FREQ="0x312"` consistent across fragment, checker, README, workflow.

---

## Execution handoff

Plan saved to:

`CleanPadavan-AC2100-main/docs/superpowers/plans/2026-07-26-ac2100-padavan-lite.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session, `executing-plans`, batch with checkpoints  

Which approach?
