# EdenNX Ocarina iOS

Experimental work toward running **The Legend of Zelda: Ocarina of Time, Switch 2 edition, on iPhone Air**, using [seedds/nxnative](https://github.com/seedds/nxnative). This is a source contribution and research repository, **not a ready-to-install game or a finished 30 fps release**.

Technical focus: **Nintendo Switch 2 / NVIDIA Ampere shader translation through SPIR-V to Apple Metal**, native runtime adaptation, GPU rendering correctness and frame pacing on **iOS and Apple Silicon**.

**Status: 7 November 2026.** The game has run on a physical iPhone, including exterior gameplay in Kokiri Forest. Sustained smoothness and intermittent rendering flashes remain unresolved.

## What works, and what remains

| Area | Observed state |
|---|---|
| Boot and gameplay | Menu, save loading, interiors and exterior gameplay reached on the tested iPhone |
| French | Game language configured and exercised in French |
| Frame-rate controller | Build-gated native 30 fps stepping integrated; brief 30 fps exterior windows observed at normal game speed |
| Sustained performance | One prolonged post-warmup run: **23.39 displayed fps over 16,460 frames**, GPU median **36.122 ms**, displayed interval p95 **66.691 ms**, p99 **100.036 ms** |
| White flashes | Still present, reported first on foreground vegetation and later across the scene; HUD remains readable |
| Presentation buffering | Two-texture ring exercised; improves some pacing observations in a combined configuration, but does not eliminate flashes |
| Draw distance / LOD | Trials at 75% did not establish a reproducible sufficient gain; original distances retained |
| Wider fullscreen | Current aspect-preserving 16:9 view fits the available height; true wider rendering without crop/stretch remains unimplemented |

These are observations from limited local tests, not a general compatibility or performance guarantee. Heat and instrumentation differed between some runs. An external cooler has not been evaluated.

## Current development

The previous installed local chain, `53eff8fc562a`, includes work on Metal end barriers, compatible depth-image storage reuse, mesh primitive-index bounds and LDSM subgroup synchronization. Its complete shader build retained **42,845 previously available primary keys**. Nine earlier failures remained out of 42,854 captures; this is not a claim that all shaders compile.

The zero-initialization candidate `f14457ae7de2` completed with all 42,845 primary keys, but acceptance rejected one lost mixed float/integer fragment-output entry. The classifier had mistaken an empty braced zero initializer for integer-format evidence. This source export now treats it like literal zero and includes a regression that fails before the correction. The replacement local chain **`5fb5cc699875` completed its full Mac/iOS build and retained all 42,845 primary keys, all variants and matching reflection metadata**. Its signed Release app is now installed and booted on the test phone with matching tables and pipeline cache. Exterior visual/performance comparison is in progress; no flash fix or sustained 30 fps is established by these build checks. The prolonged 23.39 fps baseline above belongs to the previous chain.

The source export also carries earlier ports already present in the working tree. Not every change is new to this experiment or individually established as a performance improvement.

## Repository contents

- `overlay/`: changed **text sources and tests**, at upstream-relative paths.
- `patches/ocarina-source.patch`: the same source delta against upstream commit `b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb`.
- `source-manifest.json`: base, audited source paths and patch checksum.
- `config/iphone.env.example`: portable example without device IDs, signing identity or local paths.
- [BUILDING.md](BUILDING.md): how to apply sources and rebuild a consistent translator/shader chain.
- [docs/TESTING.md](docs/TESTING.md): checks performed and known gaps.
- [docs/INDEPENDENT_CHECKS.md](docs/INDEPENDENT_CHECKS.md): reviewed video/CPU investigations and their limits.
- `tools/check_public_export.py`: checks the publication boundary; no game needed.

**No ROM/package, Nintendo executable, firmware, decryption key, save, game shader library, proprietary game asset, GPU capture, signed app, certificate or provisioning profile is supplied.** Private logs, videos, screenshots, machine paths, device identifiers and signing settings are not included. Each developer must independently supply data they are authorized to use; do not open issues or pull requests containing those files.

## Contributing

Keep changes and synthetic fixtures independent of game assets. Report frame times and actual display intervals alongside fps, with scene, duration, thermal conditions and diagnostic overhead. Avoid claims of stable 30 fps from a short window or of fixed flashes from compile success alone.

Before proposing a change, read upstream's `AGENTS.md`, run relevant tests, and preserve synchronization and shader-chain consistency. Priorities are rendering correctness, sustained 30 fps and reproducible measurements. See [docs/STATUS.md](docs/STATUS.md) for the next decisive checks.

## Attribution

Built on nxnative by seedds, under the MIT license. Applicable original notices are retained; translator source changes refer to the vendored Ryujinx/Spv.Generator code, whose notices are in `licenses/`. This is an independent community project, not affiliated with Nintendo or the original game's publisher. No game artwork is used for this repository's presentation.
