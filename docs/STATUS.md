# Work remaining

1. Finish the full initialization-candidate shader reconstruction, compare exact keys and finalized reflection, and verify matching library, host, constant-extent tables and archive stamps.
2. Test that candidate in the same exterior scene, both immediately and over a longer run. Obtain visual evidence for the foreground plant and full-scene flashes. Keep a rollback; compare performance before adoption.
3. Reach sustained 30 displayed fps with normal game speed, recording long-frame tails and thermal conditions. The prolonged reference remains 23.39 displayed fps.
4. Complete independent synthetic Ampere coverage and a VFR-aware video flash detector. Those investigations were still in progress at this export.
5. Restore a fully executable graphics test suite and obtain broader regression evidence before describing the work as validated generally.
6. Evaluate real wider-aspect rendering and HUD support after correctness/performance; stretching or cropping the existing 16:9 image does not satisfy the fullscreen request.

NVIDIA Ampere architecture papers can guide semantic tests and performance hypotheses. Desktop/data-center specifications do not by themselves prove Switch 2 behavior, a correct Metal mapping or an fps gain on a phone. FP16 conversion, discarded attachment contents, warp/SIMD correspondence and MetalFX substitution require evidence from the actual translated code and its data dependencies.
