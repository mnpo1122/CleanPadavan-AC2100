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
