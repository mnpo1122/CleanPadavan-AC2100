# Design: Redmi AC2100 Padavan 4.4 Lite (OC 1000)

Date: 2026-07-26  
Status: approved  
Approach: **B — in-repo config overlay**

## Goal

Build a **stable, minimal Padavan firmware** for **Redmi AC2100 (RM2100)**:

- Latest Padavan kernel line: **4.4** (`MeIsReallyBa/padavan-4.4`)
- **CPU overclock ~1000 MHz** (compile-time)
- **Pure router + IPv6 only** — no extra plugins
- **Hardware accel**: keep **SFE** (and Flow Offload if present in tree)
- **No SSH** — Web UI management only
- GitHub Actions → `.trx` artifact + Release

Non-goals: OpenWrt, dual 3.4/4.4, RustDesk on-router, HTTPS admin, kernel HZ/NO_HZ tuning, Entware.

## Constraints

| Item | Choice |
|------|--------|
| Priority | Extreme size / purity |
| SoC | MT7621A, 128 MB RAM |
| Source | `https://github.com/MeIsReallyBa/padavan-4.4.git` branch `main` |
| Product ID | `RM2100` |
| SSH | None |
| OC | Mild 1000 MHz |

Padavan’s newest kernel in-tree is **linux-4.4.x**. Newer 5.x/6.x requires leaving Padavan (OpenWrt/ImmortalWrt) — out of scope.

## Architecture

```
CleanPadavan-AC2100-main/
  .github/workflows/build-padavan.yml
  configs/RM2100.config              # userspace firmware template overlay
  configs/kernel-oc.fragment         # MT7621 OC Kconfig fragment
  docs/superpowers/specs/...
  README.md
```

Build flow (CI):

1. Checkout this repo (overlays + workflow).
2. Install Ubuntu 22.04 build deps (existing apt set).
3. `git clone --depth=1` MeIsReallyBa/padavan-4.4 → `$WORK_DIR`.
4. Run `toolchain-mipsel/dl_toolchain.sh`.
5. Overlay:
   - `cp configs/RM2100.config` → `trunk/configs/templates/RM2100.config`
   - Append `configs/kernel-oc.fragment` into `trunk/configs/boards/RM2100/kernel-4.4.x.config` (idempotent: strip prior `CONFIG_MT7621_OC` / `CONFIG_MT7621_CPU_FREQ` lines first).
6. `cd trunk && cp templates/RM2100.config .config && fakeroot ./build_firmware RM2100`.
7. Collect `trunk/images/*.trx` → Release `vYYYYMMDD-4.4-oc1000-lite`.

No 3.4 path. No long sed chains for feature toggles — config file is source of truth.

## Overclock

Upstream already supports OC in `arch/mips/ralink/mt7621.c`:

- `CONFIG_MT7621_OC=y`
- `CONFIG_MT7621_CPU_FREQ` = hex string written into MPLL (`sscanf` → `DRAMC_REG_MPLL18`)

Fragment:

```
CONFIG_MT7621_OC=y
CONFIG_MT7621_CPU_FREQ="0x312"
```

`0x312` is the community mild-OC value targeting ~1000 MHz. Verify post-boot via dmesg `CPU Clock: …MHz`. If off-target, adjust hex only — no other design change.

Risk: board-dependent instability → recover via Breed. Optional 880 MHz workflow input is **deferred**.

## Userspace template (`configs/RM2100.config`)

Base: upstream `trunk/configs/templates/RM2100.config`, then harden for lite.

### Keep / force on

- `CONFIG_LINUXDIR=linux-4.4.x`
- `CONFIG_FIRMWARE_PRODUCT_ID="RM2100"`
- `CONFIG_FIRMWARE_ENABLE_IPV6=y`
- `CONFIG_FIRMWARE_INCLUDE_SFE=y`
- `CONFIG_FIRMWARE_INCLUDE_LANG_CN=y`
- Core routing stack as provided by Padavan for RM2100 (WiFi MT7603E + MT7615E profiles unchanged)

### Force off (size + attack surface)

USB / storage / printer / media / download / VPN / proxy plugins (already mostly `n` upstream — keep `n`).

Additional cuts vs upstream template:

| Option | Upstream-ish | Lite |
|--------|--------------|------|
| OpenSSH | y | **n** |
| SFTP | y | **n** |
| Dropbear | n | **n** |
| curl | y | **n** |
| htop | y | **n** |
| iperf3 | y | **n** |
| mtr | y | **n** |
| socat | y | **n** |
| vlmcsd | y | **n** |
| IPSET | y | **n** |
| EAP_PEAP | y | **n** |
| OPENSSL_EXE | y | **n** |
| HTTPS | n | **n** |
| FFMPEG_NEW | y | **n** |
| Flow Offload (if key exists) | vary | **y** |

Defaults unchanged unless later requested: LAN `192.168.123.1`, user/pass `admin`/`admin`, WiFi password `1234567890`.

## Performance knobs (in scope)

| Knob | Action |
|------|--------|
| SFE | Keep `y` |
| Flow Offload | Ensure `y` when symbol exists in template |
| OC 1000 | Kernel fragment |
| Strip tools/plugins | Template |

Out of scope: HZ / NO_HZ / PREEMPT changes, custom WiFi cal, RustDesk hbbs/hbbr on router.

## CI / Release

- Trigger: `workflow_dispatch` only
- Runner: `ubuntu-22.04`
- Permissions: `contents: write` (Release upload)
- Tag: `v${DATE}-4.4-oc1000-lite`
- Release body must state: Padavan 4.4, OC ~1000 MHz, SFE, IPv6, no SSH, pure router

Replace or supersede `build-Gemini.yml` with `build-padavan.yml` (single workflow).

## Risks & recovery

| Risk | Mitigation |
|------|------------|
| OC unstable | Breed reflash stock/previous trx; later add 880 option |
| Wrong MPLL hex | Check `CPU Clock` in dmesg; fix fragment only |
| No SSH brick | Web UI + serial / Breed only — documented in README |
| Upstream template drift | Diff overlay against upstream on bump; pin by commit optional later |
| Build break Ubuntu 22.04 | Keep known-good apt deps; add patches only if compile fails |

## Implementation order (for plan skill)

1. Add `configs/RM2100.config` and `configs/kernel-oc.fragment`
2. Rewrite workflow → clone 4.4 only, apply overlays, build, release
3. Update README (usage, defaults, OC warning, no SSH, no RustDesk-on-router)
4. Remove obsolete dual-version docs/workflow name

## Success criteria

- Actions produces a flashable `.trx` for RM2100
- Image boots with IPv6 + WiFi + NAT; SFE path available
- dmesg shows CPU clock near 1000 MHz when OC applied
- No SSH/OpenSSH/Dropbear in firmware config
- No download/VPN/proxy plugins enabled in config
