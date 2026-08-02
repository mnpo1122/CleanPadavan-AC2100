#!/usr/bin/env python3
"""Inspect an ImmortalWrt tree for RM2100 build readiness."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = (
    "target/linux/ramips/dts/mt7621_xiaomi_redmi-router-ac2100.dts",
    "target/linux/ramips/dts/mt7621_xiaomi_router-ac2100.dtsi",
    "target/linux/ramips/image/mt7621.mk",
    "package/kernel/mt76/Makefile",
    "package/network/config/firewall4/Makefile",
    "package/kernel/linux/modules/netsupport.mk",
)
CLOCK_SOURCE_PATTERNS = (
    "target/linux/ramips/files-*/drivers/clk/ralink/clk-mt7621.c",
    "target/linux/ramips/files-*/**/clk-mt7621.c",
)
CLOCK_PATCH_PATTERNS = (
    "target/linux/ramips/patches-*/312-MIPS-ralink-add-cpu-frequency-scaling.patch",
)
HNAT_PATTERNS = ("kmod-ramips-hnat", "mtkhnat", "shortcut-fe", "fast-classifier")


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def kernel_version(root: Path) -> str:
    path = root / "target/linux/ramips/Makefile"
    if not path.is_file():
        return "UNKNOWN"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"KERNEL_PATCHVER\s*:=\s*(.+)", line)
        if match:
            return match.group(1).strip()
    return "UNKNOWN"


def find_path(root: Path, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        matches = sorted(root.glob(pattern))
        if matches:
            return str(matches[0].relative_to(root))
    return "NOT_FOUND"


def package_exists(root: Path, package: str) -> bool:
    return any(
        (root / relative).is_dir()
        for relative in (
            f"package/network/utils/{package}",
            f"package/kernel/{package}",
            f"feeds/luci/applications/{package}",
        )
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: inspect-upstream.py /path/to/immortalwrt", file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"ERROR: source directory does not exist: {root}", file=sys.stderr)
        return 1

    errors = [f"MISSING: {path}" for path in REQUIRED_FILES if not (root / path).is_file()]
    image = root / "target/linux/ramips/image/mt7621.mk"
    if image.is_file() and "xiaomi_redmi-router-ac2100" not in image.read_text(
        encoding="utf-8", errors="replace"
    ):
        errors.append("MISSING: xiaomi_redmi-router-ac2100 profile")

    clock = find_path(root, CLOCK_SOURCE_PATTERNS)
    clock_patch = find_path(root, CLOCK_PATCH_PATTERNS)
    if clock == "NOT_FOUND" and clock_patch == "NOT_FOUND":
        errors.append("MISSING: MT7621 clock source and clock patch path")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    netsupport = root / "package/kernel/linux/modules/netsupport.mk"
    netfilter = root / "package/kernel/linux/modules/netfilter.mk"
    fullcone = root / "package/network/utils/fullconenat-nft"
    hnat = sorted(
        str(path.relative_to(root))
        for pattern in HNAT_PATTERNS
        for path in root.glob(f"package/**/{pattern}*")
    )
    flow_text = netfilter.read_text(encoding="utf-8", errors="replace") if netfilter.is_file() else ""
    flow = [name for name, marker in (("nf-flow", "nf-flow"), ("NF_FLOW_TABLE", "NF_FLOW_TABLE")) if marker in flow_text]
    bbr = bool(re.search(r"define KernelPackage/tcp-bbr\b", netsupport.read_text(encoding="utf-8", errors="replace")))

    print(f"IMMORTALWRT_COMMIT={git_head(root)}")
    print(f"KERNEL_PATCHVER={kernel_version(root)}")
    print("RM2100_DTS=target/linux/ramips/dts/mt7621_xiaomi_redmi-router-ac2100.dts")
    print("RM2100_IMAGE=target/linux/ramips/image/mt7621.mk")
    print("MT76_MAKEFILE=package/kernel/mt76/Makefile")
    print(f"CLOCK_SOURCE={clock}")
    print("FIREWALL4_MAKEFILE=package/network/config/firewall4/Makefile")
    print(f"FLOW_OFFLOAD={','.join(flow) if flow else 'NONE'}")
    print(f"FULLCONE={'YES' if fullcone.is_dir() else 'NOT_FOUND'}")
    print(f"BBR={'YES' if bbr else 'NOT_FOUND'}")
    print(f"HNAT_PACKAGES={','.join(hnat) if hnat else 'NONE'}")
    print("WIFI_SCRIPTS=package/network/config/wifi-scripts/files/lib/netifd/wireless/mac80211.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
