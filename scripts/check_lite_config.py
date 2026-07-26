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
