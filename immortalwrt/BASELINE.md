# ImmortalWrt RM2100 baseline

Recorded: 2026-08-02

- Source: `https://github.com/immortalwrt/immortalwrt`
- Release: `v25.12.1`
- Build source: `v25.12.1` tag
- Ramips kernel patch version: `6.12`
- Board: `xiaomi,redmi-router-ac2100`
- Image profile: `xiaomi_redmi-router-ac2100`
- WAN logical device: `wan`
- LAN logical devices: `lan1 lan2 lan3`
- 5 GHz radio: MT7615
- 2.4 GHz radio: MT7603
- WiFi script: `package/network/config/wifi-scripts/files/lib/netifd/wireless/mac80211.sh`
- Firewall: `package/network/config/firewall4/Makefile`
- Software flow package: `kmod-nft-offload`
- FullCone kernel package: `kmod-nft-fullcone`
- FullCone source package: `fullconenat-nft`
- FullCone firewall4 keys: `defaults.fullcone` and `defaults.fullcone6`
- BBR package: `kmod-tcp-bbr`
- MT7621 HNAT/PPE/SFE packages: none found in mainline
- MT7621 clock source: Linux `drivers/clk/ralink/clk-mt7621.c`; shallow source tree did not contain the expanded kernel source

The build must preserve the native DTS, EEPROM/calibration data, NAND layout, MAC addresses, and DSA mapping. The workflow records the exact source commit again at build time.

FullCone IPv4 is enabled by default through firewall4's supported UCI key. FullCone IPv6 remains disabled because routed IPv6 does not require NAT.
