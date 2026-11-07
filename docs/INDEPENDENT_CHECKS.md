# Independent investigations — reviewed 2026-11-07

Two independent investigations delivered a video flash detector and a CPU Ampere bench. Their original private reports, video, images, raw outputs and captured shader data are not distributed here.

## Video

Five synthetic detector tests passed again during review. In the tested clip, all 3,409 decoded-frame timestamps matched the nonnegative packet timestamps used by the detector. This verifies alignment for that clip, not every codec or reordered stream.

Major scene flashes occur around 52.985, 53.652 and 72.890 seconds, while HUD features remain visible. This constrains the investigation toward scene-specific rendering/processing before or separately from HUD composition. It does **not** identify the geometry pass uniquely or establish that earlier foreground-plant instability causes the later flashes. Post-processing and resource corruption remain possible.

The detector's so-called engine fps comes from thresholding image differences in one region. It is an estimate of visible updates, not a direct measurement of engine work or actual display presents. Host presentation timings remain the performance reference.

## Ampere

The audit identifies one active tensor shader in the examined capture: 192 HMMA operations, m16n8k16 with f16 accumulation, with no LDSM/MOVM on that path. Twelve tests of the interpreted deployed HMMA template and four tests of a Python mirror of fallback formulas passed again during review.

The bench has explicit limitations: some Apple matrix load/store/rounding assumptions and PTX fragment references were not independently verified against their specifications by the investigator. The fallback mirror does not execute C#. Passing these tests is conditional model evidence, not complete hardware conformance or phone rendering acceptance.

A modeled half-precision overflow case motivates checking non-finite outputs in an isolated replay. No NaN/inf corruption was observed in the actual game by this investigation, and no such correction has been applied. A float32 comparison would be an experiment for the captured inputs, not a demonstrated fix or a general falsification across all scenes.

## Specification audit follow-up

A later audit verified PTX fragment layouts and the FP16 precision restrictions
against [NVIDIA PTX ISA 9.5](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html#warp-level-matrix-instructions-mma).
FP16 accumulation does not prescribe a unique rounding order or mode. Apple
matrix load/store origin and accumulation hypotheses still require targeted
hardware checks. The [Metal language specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf)
distinguishes fast and relaxed math; microtests must record and compare both.

The revised CPU oracle initially still used a nearest-rounding error unit.
Review reproduced two false rejections with finite directed-rounding models.
An isolated review copy uses a wider, error-propagating envelope with explicit
finite-normal IEEE assumptions; it is not a universal PTX/SASS conformance
criterion. Six specification tests, two directed-rounding regressions, twelve
HMMA tests and four mirror tests passed in that copy. Exact layout checks and
conditional overflow/subnormal observations remain separate. No production
shader, runtime or device configuration was changed from these results.

## Isolated Metal hardware follow-up

The actual template hash was checked against the active source. An isolated
Apple M4 experiment was reproduced in explicit fast and relaxed modes with
small synthetic buffers. Exact layout/integer cases agreed. For a constructed
+80000 partial sum followed by -80000, the half-result path produced+Inf and the
float32-accumulator comparison produced 0 in both modes. This is a local observed
precision difference, not a game defect or a demonstrated flash cause.

Review corrected the chain experiment: its two variants originally shared the
half accumulator on subsequent steps. With independent four-step recurrences,
all 32,768 scalar outputs per variant remained finite and the maximum difference
was 0.0068359375. The workload is 256 matrices of 16 x 8 per scenario, not 32,768 matrices.
Special-value observations are not a general IEEE conformance claim, and no
phone-performance conclusion is drawn.

The proposed real-input capture plan requires revision against actual runtime
reflection, binding namespaces and GPU-ordered readback. Existing local capture
resources have not yet yielded verified dispatch inputs from a flash. No new
production shader or capture hook was introduced from this experiment.
