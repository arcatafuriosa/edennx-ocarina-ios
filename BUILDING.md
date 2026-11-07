# Applying and building the source contribution

This repository contains source changes, not an IPA or game data. Start from the exact upstream base; do not apply it to an arbitrary latest checkout without reviewing conflicts.

```sh
git clone https://github.com/arcatafuriosa/edennx-ocarina-ios.git
git clone https://github.com/seedds/nxnative.git nxnative-dev
git -C nxnative-dev checkout --detach b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb
git -C nxnative-dev apply --check ../edennx-ocarina-ios/patches/ocarina-source.patch
git -C nxnative-dev apply ../edennx-ocarina-ios/patches/ocarina-source.patch
```

The `overlay/` tree is an alternative to applying the patch; do not apply both. It is not a standalone upstream checkout. Upstream history and dependencies remain in the separate `nxnative-dev` repository.

## Toolchain consistency is required

Read upstream's README, AGENTS.md, `docs/development.md` and `docs/agents/04-graphics.md`. The source base requests macOS 26.6+, Xcode 27.2 and arm64 Python 3.12+. The translator project targets .NET 10. Build and signing require the appropriate Apple tools and your own authorized setup.

Generated translator DLLs, PDBs, tool fingerprints and shader-chain headers are intentionally not published here. The changed C# source must be compiled before using it. Follow upstream's translator rebuild procedure for `dm/gfx/tools/dmsh_xlate/dmsh_xlate.csproj`, deploy the resulting tool coherently and preserve its architecture requirements. A fresh `dotnet publish` has different fingerprints from the bundled tool; it must not silently reuse that tool's old lock.

After deploying the intended translator and compiler tools, run from the upstream checkout:

```sh
python3 dm/gfx/tools/tool_lock.py --update-lock
python3 dm/gfx/tools/tool_lock.py --check-tools
python3 dm/gfx/tools/dmsh_chain.py --header
```

Then rebuild the game's **complete** shader library for the intended platforms with the upstream tooling and your own authorized local inputs. A rebuild on another toolchain may have a different chain ID from the local research candidate; that is expected. Do not force its name to `f14457ae7de2` or mix libraries from `53eff8fc562a` with a new host.

The full shader run also generates `c1_full.tsv` and `cb_extent.tsv`; ensure the Xcode copies in `Gen/dm` name the same chain/profile digest. Rebuild pipeline archives for the intended GPU and OS major version, then rebuild the host/app. Regenerate machine-specific Xcode resources instead of copying another machine's paths or signing configuration.

No fresh end-to-end build from this public export has been established. The instructions describe the required integration path and are not a claim of a ready-to-run port. The precise local research results and limits are in `docs/TESTING.md`.

## Conservative runtime example

`config/iphone.env.example` records the portable test configuration, not an installation command. Experimental depth feedback and dispatch overlap are explicitly disabled despite the source profile exposing experimental behavior. Persist options using the host's supported environment mechanism and verify them in the actual boot log. Use a separate save copy for experiments and avoid overwriting a current save.
