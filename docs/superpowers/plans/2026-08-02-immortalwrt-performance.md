# Redmi AC2100 ImmortalWrt Performance Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one minimal ImmortalWrt RM2100 image using the latest maintained source, Software Flow Offloading, optional FullCone NAT, BBR, measured MT7621 OC1000, and aggressive legal mt76 WiFi defaults without importing legacy HNAT/SFE code.

**Architecture:** Keep ImmortalWrt's native RM2100 DTS, DSA, firewall4, and mt76 stack. A workflow clones ImmortalWrt `master`, applies only verified local patches and filesystem overlays, builds the native RM2100 image, runs static invariants, then publishes an explicitly experimental image until hardware soak validation passes.

**Tech Stack:** ImmortalWrt `master`, Linux 6.18 ramips/mt7621, GitHub Actions, firewall4/nftables, mt76, `odhcp6c`, `odhcpd`, Python 3 stdlib checks.

## Global Constraints

- Target: `xiaomi,redmi-router-ac2100` / RM2100; preserve native DTS, EEPROM, calibration, NAND, MAC, and DSA mapping.
- Source: `https://github.com/immortalwrt/immortalwrt`, branch `master`; resolve and record the exact commit in each build.
- WAN: DHCP behind a routed optical modem.
- IPv6: Native DHCPv6-PD using `odhcp6c` + `odhcpd`.
- Acceleration: nftables Software Flow Offloading; no MT7621 HNAT/PPE, `mtkhnat`, swconfig, or Padavan SFE port.
- FullCone NAT: include support when the checked-out firewall4 provides it; enabled by default and user-toggleable off for compatibility.
- OC: one experimental OC1000 image only; no DTS-only fake frequency; no voltage modification.
- WiFi: upstream mt76 first; tune UCI/mac80211/hostapd before any C patch.
- BBR: compile support and set router-local congestion control; do not claim LAN forwarding acceleration.
- Remove: proxy/VPN/scientific networking, downloaders, Samba/FTP/DLNA, USB/storage/printing, containers, SQM/Cake/QoS, AdGuard/third-party DNS, compilers, headers, packet capture, and debug tools.
- Keep: LuCI, netifd/procd/ubus, dnsmasq, firewall4/nftables, IPv6 services, mt76 firmware/drivers, watchdog, sysupgrade/recovery, and minimal diagnostics.
- Do not delete or stage unrelated pre-existing untracked files such as `.claude/`.
- Do not publish the image as stable before WAN, IPv6-PD, WiFi, reboot, link-flap, and 24-hour soak checks pass.

---

## File map

| Path | Responsibility |
|---|---|
| `immortalwrt/.github/workflows/build-immortalwrt.yml` | Reproducible clone, patch, config, build, artifact/release |
| `immortalwrt/patches/0001-mt7621-oc-1000mhz.patch` | Early PLL experiment only; added only after source validation |
| `immortalwrt/files/etc/config/network` | DHCP WAN, LAN, DHCPv6-PD defaults |
| `immortalwrt/files/etc/config/firewall` | SFO + FullCone options on by default; FullCone runtime disable toggle documented |
| `immortalwrt/files/etc/config/wireless` | RM2100 2.4/5 GHz performance defaults |
| `immortalwrt/files/etc/sysctl.d/99-performance.conf` | BBR and bounded conntrack settings only |
| `immortalwrt/scripts/check-immortalwrt-config.py` | Static overlay and package invariant check |
| `immortalwrt/scripts/inspect-upstream.py` | Verify source paths/symbols before patching; no firmware mutation |
| `immortalwrt/README.md` | Build, flash, recovery, and experimental warnings |

No `mt76` C patch is created in the first implementation. If profiling later proves a driver defect, it becomes a separate reviewed task and patch.

---

## Task 1: Pin and inspect ImmortalWrt baseline

**Files:**
- Create: `immortalwrt/scripts/inspect-upstream.py`
- Create: `immortalwrt/BASELINE.md`
- Test: `immortalwrt/scripts/inspect-upstream.py`

**Interfaces:**
- `inspect-upstream.py` accepts one repository root argument and exits nonzero when required RM2100, mt76, clock, firewall4, or flow-offload paths are absent.
- It prints the source commit, kernel patch version, RM2100 DTS/image paths, clock source path, and discovered flow-offload symbols.

- [ ] **Step 1: Create the inspector test fixture contract**

The script must check these exact relative paths:

```text
target/linux/ramips/dts/mt7621_xiaomi_redmi-router-ac2100.dts
target/linux/ramips/dts/mt7621_xiaomi_router-ac2100.dtsi
target/linux/ramips/image/mt7621.mk
drivers/clk/ralink/clk-mt7621.c
package/network/config/firewall4/Makefile
package/kernel/mt76/Makefile
```

For `drivers/clk/ralink/clk-mt7621.c`, resolve under `target/linux/ramips/files-*` or the checked-out kernel tree; do not assume one path without checking.

- [ ] **Step 2: Implement the inspector**

Use Python stdlib only. Required output fields:

```text
IMMORTALWRT_COMMIT=<40-hex>
KERNEL_PATCHVER=<value read from target/linux/ramips/Makefile>
RM2100_DTS=<relative path>
RM2100_IMAGE=<relative path containing redmi-router-ac2100>
MT76_MAKEFILE=<relative path>
CLOCK_SOURCE=<relative path>
FIREWALL4_MAKEFILE=<relative path>
FLOW_OFFLOAD=<found symbols/files or NONE>
```

- [ ] **Step 3: Run against a shallow clone**

```bash
git clone --depth=1 --branch master https://github.com/immortalwrt/immortalwrt.git /tmp/immortalwrt-inspect
python immortalwrt/scripts/inspect-upstream.py /tmp/immortalwrt-inspect
git -C /tmp/immortalwrt-inspect rev-parse HEAD
```

Expected: all RM2100/mt76/firewall4/clock fields resolve; if clock source path differs, record the actual path rather than guessing.

- [ ] **Step 4: Record baseline**

`BASELINE.md` must include the resolved commit, kernel patch version, exact image profile name, exact required package names, clock source path, and a statement that no MT7621 HNAT/PPE package was found in mainline.

- [ ] **Step 5: Commit**

```bash
git add immortalwrt/scripts/inspect-upstream.py immortalwrt/BASELINE.md
git commit -m "build(ac2100): inspect ImmortalWrt RM2100 baseline"
```

---

## Task 2: Build minimal package and config overlay

**Files:**
- Create: `immortalwrt/files/etc/config/network`
- Create: `immortalwrt/files/etc/config/firewall`
- Create: `immortalwrt/files/etc/config/wireless`
- Create: `immortalwrt/files/etc/sysctl.d/99-performance.conf`
- Create: `immortalwrt/scripts/check-immortalwrt-config.py`
- Test: `immortalwrt/scripts/check-immortalwrt-config.py`

**Interfaces:**
- The checker consumes the four overlay files and a package manifest, then exits 0 only when required services/settings are present and banned packages/settings are absent.

- [ ] **Step 1: Write network overlay**

Use UCI defaults with WAN DHCP and IPv6 PD:

```uci
config interface 'lan'
        option device 'br-lan'
        option proto 'static'
        option ipaddr '192.168.1.1'
        option netmask '255.255.255.0'
        option ip6assign '60'

config interface 'wan'
        option device 'wan'
        option proto 'dhcp'

config interface 'wan6'
        option device '@wan'
        option proto 'dhcpv6'
        option reqaddress 'try'
        option reqprefix 'auto'
```

Do not hardcode an incorrect DSA device if the inspector finds the RM2100 target uses a different logical WAN name; use the board's native generated network configuration and overlay only protocol/options.

- [ ] **Step 2: Write firewall overlay**

Set Software Flow Offloading and FullCone NAT on by default:

```uci
config defaults
        option input 'REJECT'
        option output 'ACCEPT'
        option forward 'REJECT'
        option synflood_protect '1'
        option flow_offloading '1'
        option flow_offloading_hw '0'
        option fullcone '1'
```

If the checked firewall4 version uses a different FullCone option name, use its documented option and record it in `BASELINE.md`; never invent a silently ignored key. Do not enable legacy HNAT or add manual nftables flowtables.

- [ ] **Step 3: Write WiFi overlay**

Use native radio names and board-generated paths. Defaults:

```uci
config wifi-device 'radio0'
        option band '2g'
        option htmode 'HT20'
        option country '<legal-country-required>'
        option wmm '1'
        option disabled '0'

config wifi-device 'radio1'
        option band '5g'
        option htmode 'VHT80'
        option country '<legal-country-required>'
        option wmm '1'
        option disabled '0'
```

The implementation must replace `<legal-country-required>` with an explicit user-selected legal country before build; it must not bypass regulatory limits. Enable documented AMPDU/short-GI/LDPC/STBC/beamforming options only when `iw`/driver capability inspection confirms them. Do not force DFS bypass, unsupported MCS, calibration edits, or a fixed congested channel.

- [ ] **Step 4: Write bounded sysctl overlay**

Enable BBR only if the built kernel contains it:

```text
net.ipv4.tcp_congestion_control=bbr
```

Do not add arbitrary TCP buffer, UDP timeout, RPS/XPS, or irqbalance tuning. Any conntrack limit must be selected from available RAM and documented in `BASELINE.md`.

- [ ] **Step 5: Write checker**

The checker must assert:

```text
network has wan proto dhcp
network has wan6 proto dhcpv6 and reqprefix auto
firewall flow_offloading=1
firewall flow_offloading_hw=0
FullCone exists and is explicitly enabled by default; a documented disable toggle exists
wireless has 2g + HT20 and 5g + VHT80
wireless has WMM enabled
sysctl requests BBR
banned package names are absent from the selected package list
HNAT/mtkhnat/swconfig/SFE strings are absent from overlays
```

- [ ] **Step 6: Test positive and negative cases**

```bash
python immortalwrt/scripts/check-immortalwrt-config.py --root immortalwrt
# Expected: OK
```

Copy the overlay to a temporary directory, change `flow_offloading_hw '0'` to `1`, run the checker, and expect exit 1 mentioning hardware offload. Restore the repository unchanged.

- [ ] **Step 7: Commit**

```bash
git add immortalwrt/files immortalwrt/scripts/check-immortalwrt-config.py
git commit -m "feat(ac2100): add ImmortalWrt minimal network and WiFi profile"
```

---

## Task 3: Verify and implement early PLL OC patch

**Files:**
- Create only after Task 1 evidence: `immortalwrt/patches/0001-mt7621-oc-1000mhz.patch`
- Modify only the resolved MT7621 clock/early-init source path
- Modify: `immortalwrt/scripts/check-immortalwrt-config.py`

**Interfaces:**
- Patch must program the actual MT7621 PLL before timer consumers depend on the final rate, preserve reserved bits, log old/new register values, and fail closed on an unexpected register state.
- Checker must reject a PLL patch that changes only DTS `clock-frequency`.

- [ ] **Step 1: Trace current clock initialization**

Read the exact source resolved by Task 1 and document:

```text
CPU PLL register and masks
clock init call order
GIC timer registration order
bus clock derivation
MIPS delay calibration point
```

Do not write the patch while any item is unknown.

- [ ] **Step 2: Calculate and verify the PLL field value**

Use the source's XTAL mode, PREDIV table, FBDIV mask, and current rate formula. Add a small Python assertion script or checker that proves the selected field produces a CPU rate in the accepted 1000 MHz window for the RM2100 XTAL. Do not copy Padavan's `0x312` blindly.

- [ ] **Step 3: Write the minimal early patch**

The patch may modify only the resolved early MT7621 clock path. It must:

```text
read register
verify SoC/register precondition
update only validated PLL fields
write register
read back
log register and calculated CPU/bus rate
```

No voltage changes, DTS fake rate, WiFi changes, Ethernet changes, or runtime sysfs writer.

- [ ] **Step 4: Add static safety tests**

```bash
python immortalwrt/scripts/check-immortalwrt-config.py --root immortalwrt
```

Checker must fail if the patch contains a DTS-only clock edit, `memc` writes after clock/timer initialization, HNAT/SFE symbols, or a missing readback/log path.

- [ ] **Step 5: Build and boot test before later tasks**

Required device tests:

```sh
cat /proc/cpuinfo
dmesg | grep -Ei 'clock|pll|timer|cpu|bus'
dmesg | grep -Ei 'panic|watchdog|reset|mtd|dma|ethernet'
```

Run 20 reboot cycles, DHCP WAN renewals, optical-modem reboot recovery, WAN link flap, IPv4/IPv6 throughput, concurrent TCP/UDP, and 24-hour idle/traffic soak. A failure blocks WiFi driver work and requires reverting OC to stock clock.

- [ ] **Step 6: Commit only after tests**

```bash
git add immortalwrt/patches/0001-mt7621-oc-1000mhz.patch immortalwrt/scripts/check-immortalwrt-config.py
 git commit -m "feat(ac2100): add measured MT7621 early PLL OC"
```

Do not claim this task complete from a successful compile alone.

---

## Task 4: Add BBR, FullCone toggle, and package pruning

**Files:**
- Modify: `immortalwrt/files/etc/sysctl.d/99-performance.conf`
- Modify: `immortalwrt/files/etc/config/firewall`
- Create: `immortalwrt/configs/rm2100-minimal.seed`
- Modify: `immortalwrt/scripts/check-immortalwrt-config.py`

- [ ] **Step 1: Create package seed**

The seed must explicitly retain:

```text
luci
firewall4
nftables
kmod-nft-offload
kmod-mt76-core
kmod-mt7603
kmod-mt7615e
kmod-mt7615-firmware
dnsmasq
odhcp6c
odhcpd
wpad-basic-mbedtls
```

Resolve exact package names from Task 1's source; if a name differs, record the exact source name rather than silently dropping the dependency.

- [ ] **Step 2: Remove banned packages**

The seed must explicitly exclude proxy/VPN, downloader, Samba/FTP/DLNA, USB/storage/printing, container, SQM/Cake/QoS, AdGuard, compiler/header, packet capture, and debug packages. Do not remove `opkg`/dependency plumbing unless the checked-out image build proves it is safe.

- [ ] **Step 3: Validate BBR and FullCone dependencies**

The build config must contain BBR kernel support. FullCone is packaged when supported, and runtime config is enabled by default with a documented disable toggle. The checker must distinguish “package available” from “feature enabled.”

- [ ] **Step 4: Commit**

```bash
git add immortalwrt/configs/rm2100-minimal.seed immortalwrt/files immortalwrt/scripts/check-immortalwrt-config.py
git commit -m "feat(ac2100): prune packages and add BBR FullCone support"
```

---

## Task 5: WiFi runtime profile

**Files:**
- Modify: `immortalwrt/files/etc/config/wireless`
- Modify: `immortalwrt/scripts/check-immortalwrt-config.py`

- [ ] **Step 1: Inspect generated RM2100 radios**

Boot the baseline and run:

```sh
wifi config
iw phy
iw list
uci show wireless
```

Record radio names, supported HT/VHT capabilities, supported channels, and legal country configuration.

- [ ] **Step 2: Apply only supported aggressive settings**

Enable VHT80/HT20-40 auto, WMM, aggregation, short GI, LDPC, STBC, beamforming, and radio power-save disable only where `iw list` confirms support. Keep non-DFS preference as a channel policy, not a DFS bypass.

- [ ] **Step 3: Add WiFi checks**

Checker must reject:

```text
country unset or invalid
unsupported htmode
power above legal configured limit
DFS disabled by a bypass flag
calibration/EEPROM modifications
beacon interval below 100 ms
forced minimum-rate removal
```

- [ ] **Step 4: Test radios**

Measure 2.4 GHz/5 GHz throughput, latency, reconnect behavior, mixed-client stability, and IoT compatibility. Run at least one overnight client soak. A throughput gain with unacceptable disconnects is a failure.

- [ ] **Step 5: Commit**

```bash
git add immortalwrt/files/etc/config/wireless immortalwrt/scripts/check-immortalwrt-config.py
git commit -m "feat(ac2100): tune RM2100 mt76 WiFi defaults"
```

No C patch in this task.

---

## Task 6: GitHub Actions build workflow

**Files:**
- Create: `immortalwrt/.github/workflows/build-immortalwrt.yml`
- Modify: `immortalwrt/scripts/check-immortalwrt-config.py`

- [ ] **Step 1: Add dispatch inputs**

Inputs:

```yaml
country:
  required: true
  type: string
  description: Regulatory country code, e.g. CN
  default: CN
```

Do not accept an unchecked frequency or HNAT switch. This is one OC1000 profile with SFO and FullCone enabled by default; no HNAT switch is exposed.

- [ ] **Step 2: Build workflow**

The workflow must:

```text
checkout this overlay repository
run static checker
clone ImmortalWrt master depth=1
record git rev-parse HEAD
run source inspector
copy files/ and patches/ into the expected ImmortalWrt paths
apply package seed
make defconfig with native RM2100 profile
run make download -j4
run make -j$(nproc)
collect the native RM2100 sysupgrade/factory image
upload artifact
create release marked EXPERIMENTAL
```

Use `set -euo pipefail`, verify required files before mutation, and fail if no RM2100 image is produced. Do not call a generic image name without checking the actual image profile discovered by Task 1.

- [ ] **Step 3: Release metadata**

Include:

```text
ImmortalWrt master commit
Linux kernel patch version
RM2100 profile
OC1000 experimental warning
SFO enabled
FullCone enabled by default; disable toggle documented
HNAT not included
WiFi legal-country input
```

- [ ] **Step 4: Commit**

```bash
git add immortalwrt/.github/workflows/build-immortalwrt.yml immortalwrt/scripts/inspect-upstream.py immortalwrt/scripts/check-immortalwrt-config.py
git commit -m "feat(ac2100): add ImmortalWrt RM2100 performance workflow"
```

---

## Task 7: Documentation and final verification

**Files:**
- Create: `immortalwrt/README.md`
- Modify: `immortalwrt/BASELINE.md`

- [ ] **Step 1: Document flashing/recovery**

README must state:

```text
Use the native RM2100 image and documented Breed/sysupgrade path.
Back up factory calibration and MAC data before flashing.
OC1000 is experimental and can prevent boot.
Restore the stock-clock image if WAN, timer, watchdog, or flash errors occur.
FullCone is enabled by default and has a documented runtime disable toggle.
HNAT/SFE are not included.
BBR does not accelerate forwarded LAN TCP.
```

- [ ] **Step 2: Run all static checks**

```bash
python immortalwrt/scripts/inspect-upstream.py /path/to/immortalwrt
python immortalwrt/scripts/check-immortalwrt-config.py --root immortalwrt
python -m compileall immortalwrt/scripts
```

Expected: all exit 0.

- [ ] **Step 3: Verify clean scope**

```bash
git status --short
find immortalwrt -type f | sort
```

Only intended ImmortalWrt files may be staged. Leave unrelated `.claude/` untouched.

- [ ] **Step 4: Commit**

```bash
git add immortalwrt/README.md immortalwrt/BASELINE.md
git commit -m "docs(ac2100): document ImmortalWrt experimental build"
```

- [ ] **Step 5: Hardware acceptance**

Run the full acceptance matrix from the spec before calling the release stable. Until then, label every artifact `experimental`.

---

## Spec coverage review

| Spec requirement | Plan task |
|---|---|
| Latest ImmortalWrt/native RM2100 | 1, 6 |
| No HNAT/SFE/swconfig port | Global constraints, 1, 6 |
| SFO | 2, 6 |
| FullCone default-on/toggleable | 2, 4, 6 |
| OC1000 early PLL | 3 |
| DHCP WAN | 2 |
| DHCPv6-PD | 2, 7 |
| BBR | 2, 4 |
| Aggressive legal WiFi | 2, 5 |
| Upstream mt76 first | 5 |
| Minimal packages | 4, 6 |
| WAN/link/reboot/IPv4/IPv6/24h soak | 3, 5, 7 |
| No false stable claim | Global constraints, 6, 7 |

Placeholder scan: none. `<legal-country-required>` is an explicit implementation input contract and must be replaced by the workflow `country` input before a build; it is not valid committed runtime configuration.

Plan saved to:

`CleanPadavan-AC2100-main/docs/superpowers/plans/2026-08-02-immortalwrt-performance.md`
