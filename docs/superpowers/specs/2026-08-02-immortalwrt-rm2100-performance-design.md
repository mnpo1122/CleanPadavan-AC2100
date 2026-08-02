# Redmi AC2100 ImmortalWrt Performance Build

Date: 2026-08-02  
Status: approved direction; implementation not started

## Goal

Build one minimal ImmortalWrt firmware for Redmi AC2100 (RM2100):

- Current ImmortalWrt `master` / latest maintained kernel
- MT7621 CPU PLL target near 1000 MHz
- DHCP WAN behind a routed optical modem
- Native DHCPv6-PD (`odhcp6c` + `odhcpd`)
- nftables Software Flow Offloading enabled
- FullCone NAT enabled by default, with a documented runtime toggle to disable it if compatibility requires.
- BBR kernel support
- Aggressive but legal WiFi defaults
- No MT7621 HNAT/PPE port
- No proxy/VPN, downloader, storage/media, container, SQM, or debug packages

## Board baseline

Use ImmortalWrt's native RM2100 target without changing board data:

- `target/linux/ramips/dts/mt7621_xiaomi_redmi-router-ac2100.dts`
- `target/linux/ramips/dts/mt7621_xiaomi_router-ac2100.dtsi`
- `target/linux/ramips/image/mt7621.mk`

The DTS maps MT7615 to 5 GHz and MT7603 to 2.4 GHz. Preserve EEPROM offsets, calibration data, MAC addresses, NAND layout, DSA port mapping, and image recipe.

## Acceleration decision

Use the current DSA + firewall4 + nftables path. Do not import old MTK SDK HNAT, `mtkhnat`, swconfig, or Padavan SFE code.

Reason: current ImmortalWrt does not expose a ready MT7621 HNAT/PPE path. Old HNAT ports commonly depend on older kernels/swconfig and can conflict with DSA/firewall4. The previous WAN/optical-modem instability makes that compatibility risk unacceptable.

Keep:

- nftables flow offload
- conntrack
- GRO/GSO/checksum offload when the driver supports them
- firewall4
- optional FullCone NAT package/config, off by default

Do not add SQM/Cake/QoS: they conflict with the selected acceleration path.

Runtime verification:

```sh
nft list ruleset
cat /proc/net/nf_conntrack | grep -E 'OFFLOAD|HW_OFFLOAD'
dmesg | grep -Ei 'flow|mtk|watchdog|reset|panic'
```

## PLL overclock

ImmortalWrt's MT7621 clock driver is Linux `drivers/clk/ralink/clk-mt7621.c`. It recalculates rates but has no safe PLL write, `set_rate`, OPP, or voltage-control path.

Relevant CPU PLL register:

```text
0x1e005648
```

DTS `clock-frequency` edits are forbidden. They change the advertised rate without programming the PLL.

The OC patch must be an early-boot, board-specific change that:

1. Preserves reserved PLL bits.
2. Changes only validated FBDIV/PREDIV fields.
3. Runs before timer consumers depend on the final rate, or explicitly reinitializes affected timer state.
4. Logs the programmed register and calculated CPU/bus rate.
5. Fails closed if the expected MT7621 register state is absent.
6. Leaves Breed/bootloader recovery available.

Target: one OC1000 image, no voltage modification. “1000 MHz” is accepted only when boot logs and `/proc/cpuinfo` report the measured rate.

OC validation gates the rest of the work:

- 20 boot/reboot cycles
- WAN DHCP acquisition/renewal
- optical modem reboot recovery
- WAN cable unplug/replug recovery
- IPv4 and IPv6 throughput
- DHCPv6-PD renewal
- concurrent TCP/UDP traffic
- 24-hour idle and traffic soak
- no panic, watchdog reset, Ethernet DMA error, SPI/NAND error, or unexplained link loss

If OC fails, stop and ship a default-clock image instead. Do not hide instability with additional patches.

## Network and TCP/UDP

WAN profile:

- `proto dhcp`
- optical modem remains in router mode
- AC2100 provides downstream NAT
- Native DHCPv6-PD on WAN
- RA/DHCPv6 on LAN

Keep:

- `odhcp6c`
- `odhcpd`
- IPv6 firewall rules
- dnsmasq cache
- conntrack
- nftables flow offload
- watchdog
- BBR kernel support and `net.ipv4.tcp_congestion_control=bbr`

BBR affects TCP connections originated by the router itself. It does not change congestion control for LAN clients being forwarded through the router.

Do not add fixed RPS/XPS maps, irqbalance, arbitrary TCP buffer enlargement, or UDP timeout changes. Their MT7621 benefit is unproven and they complicate diagnosis.

## WiFi performance profile

Use upstream mt76. No C driver patch in the first build.

### 5 GHz

- VHT80
- WMM enabled
- AMPDU/aggregation enabled where supported
- short GI, LDPC, STBC, and beamforming left enabled where supported
- MU-MIMO left to driver capability/defaults
- radio power saving disabled
- legal maximum TX power
- prefer non-DFS channels without hard-coding one channel

### 2.4 GHz

- HT20/40 auto
- WMM enabled
- AMPDU/aggregation and short GI where supported
- radio power saving disabled
- prefer channels 1/6/11 through documented policy
- legal maximum TX power

Do not alter EEPROM/calibration, country limits, DFS detection, beacon interval, minimum legacy rates, or unsupported MCS. Do not force 40 MHz in congested environments.

A mt76 C patch is allowed only after a measured, reproducible limitation remains after UCI/mac80211/hostapd tuning. One isolated patch per iteration.

## Package policy

Keep:

- LuCI/Web management
- `netifd`, `procd`, `ubus`
- dnsmasq
- firewall4, nftables, netfilter flow packages
- FullCone NAT support package if available
- odhcp6c, odhcpd
- MT7603/MT7615 firmware and mt76 drivers
- watchdog
- sysupgrade/recovery support
- minimal network diagnostics
- BBR support

Remove:

- proxy/VPN/scientific-networking packages
- Aria2/Transmission/downloaders
- Samba/FTP/DLNA/media services
- USB/storage/printing support
- Docker/container runtimes
- SQM/Cake/QoS
- AdGuard and third-party DNS services
- compilers, headers, packet capture, and debug tools

Do not remove the package/dependency mechanism required by the selected release. Remove the package UI only if it can be done without breaking dependency or recovery behavior.

## Repository layout

```text
CleanPadavan-AC2100-main/
  immortalwrt/
    .github/workflows/build-immortalwrt.yml
    patches/0001-mt7621-oc-1000mhz.patch
    patches/0002-mt76-rm2100-performance.patch  # only with evidence
    files/etc/config/network
    files/etc/config/firewall
    files/etc/config/wireless
    files/etc/sysctl.d/99-performance.conf
    scripts/check-immortalwrt-config.py
```

Workflow:

1. Clone `immortalwrt/immortalwrt` branch `master`.
2. Apply the PLL patch only after source/register checks pass.
3. Apply network, firewall, sysctl, and WiFi defaults.
4. Select native RM2100 image profile.
5. Remove unwanted packages.
6. Run config/invariant checks.
7. Build and publish the image as experimental until soak tests pass.

## Implementation phases

1. Native RM2100 baseline: current kernel, stock clock, stock mt76, SFO, DHCP WAN, DHCPv6-PD.
2. PLL OC1000 patch and timer/bus validation.
3. UCI/mac80211/hostapd WiFi tuning.
4. BBR, FullCone toggle, and minimal package profile.
5. 24-hour WAN/IPv4/IPv6/TCP/UDP/WiFi soak.
6. Only if measurable WiFi limitations remain: one mt76 C patch, followed by the same soak.

## Acceptance

```sh
ubus call system board
cat /proc/cpuinfo
dmesg | grep -Ei 'clock|pll|flow|mtk|watchdog|reset|panic'
logread | grep -Ei 'wan|udhcpc|odhcp6c|odhcpd|link'
nft list ruleset
cat /proc/net/nf_conntrack | grep -E 'OFFLOAD|HW_OFFLOAD'
ip -6 route
```

The image is acceptable only when:

- DHCP WAN remains stable behind the routed modem.
- Modem/router reboot and WAN link flap recover automatically.
- DHCPv6-PD survives renewal and reboot.
- SFO rules load without firewall4 errors.
- OC rate is measured, not inferred from DTS.
- WiFi throughput improves without unacceptable client disconnects.
- No kernel panic/watchdog/Ethernet reset appears during soak.
- Removed packages are absent from the image manifest.
