#!/usr/bin/env python3
"""Validate the RM2100 ImmortalWrt overlay before CI builds it."""
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = {
    "files/etc/uci-defaults/99-rm2100-performance",
    "files/etc/sysctl.d/99-rm2100-performance.conf",
    "configs/rm2100-minimal.seed",
}
BANNED = ("hnat", "mtkhnat", "swconfig", "shortcut-fe", "fast-classifier", "sfe")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) == 2 else ".").resolve()
    errors = []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"missing {rel}")

    defaults = (root / "files/etc/uci-defaults/99-rm2100-performance").read_text(encoding="utf-8") if not errors else ""
    sysctl = (root / "files/etc/sysctl.d/99-rm2100-performance.conf").read_text(encoding="utf-8") if not errors else ""
    seed = (root / "configs/rm2100-minimal.seed").read_text(encoding="utf-8") if not errors else ""

    required_defaults = (
        "network.wan.proto='dhcp'",
        "network.wan6.proto='dhcpv6'",
        "network.wan6.reqprefix='auto'",
        "firewall.@defaults[0].flow_offloading='1'",
        "firewall.@defaults[0].flow_offloading_hw='0'",
        "firewall.@defaults[0].fullcone='1'",
        "firewall.@defaults[0].fullcone6='0'",
        "htmode='HT20'",
        "htmode='VHT80'",
        "wmm='1'",
        "__COUNTRY__",
    )
    for value in required_defaults:
        if value not in defaults:
            errors.append(f"missing default {value}")
    if "net.ipv4.tcp_congestion_control=bbr" not in sysctl:
        errors.append("BBR sysctl missing")
    for value in BANNED:
        if value in defaults.lower() or value in seed.lower():
            errors.append(f"banned feature present: {value}")
    if "CONFIG_PACKAGE_opkg" not in seed:
        errors.append("opkg policy missing")
    if "CONFIG_TARGET_ramips_mt7621_DEVICE_xiaomi_redmi-router-ac2100=y" not in seed:
        errors.append("RM2100 target missing")

    if errors:
        print("FAIL ImmortalWrt overlay check:")
        print("\n".join(f" - {error}" for error in errors))
        return 1
    print("OK ImmortalWrt overlay check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
