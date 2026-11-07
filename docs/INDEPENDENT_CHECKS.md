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

## Extended M4 fixtures and CPU-model calibration

A follow-up used 658 synthetic fixtures, separate input cases in all four
SIMD-groups, raw-bit CPU classification and explicit fast/relaxed builds.
Archived outputs were rechecked on the CPU: 588 exact cases agreed, 65 cases
met the conditional numerical envelope and four special-range cases met their
recorded criteria. Fast and relaxed outputs matched bit for bit on this set.
Origin/transpose probes select source-coordinate origins applied before
transposition on the tested M4/toolchain; portability still requires checking.

The deployed path returned 1024 for the fixture 1024 + 16 x 0.5; the comparison
returned 1032. The old CPU assumption of rounding only after each eight-term
block fails this case. A separately named observed-M4 sequential-rounding
model reproduces all 65 archived numerical cases. Two calibration regressions
failed before the model addition and passed afterward. This fits these observed
outputs; it does not uniquely establish a universal internal accumulation order.

Ten non-finite outputs in the deployed fixture run include explicitly injected
special-value cases; they are not game observations. No production shader was
changed, no iPhone execution was performed, and real dispatch inputs and a
link to the flashes remain unestablished.


## Frame pacing analysis and recommendation review

A separate standard-library CPU analyzer reproduced the prolonged baseline:
23.39 displayed fps over 16,451 valid intervals totaling 703.249 seconds. Its
six synthetic tests passed. Intervals cluster near 33.345 ms (73.83%) and
66.691 ms (24.50%); averaging instantaneous fps would misleadingly give 26.01.
These are observed distributions, not a causal diagnosis of each missed refresh.

Additional review probes expose limitations outside that baseline: short-session
resets can merge runs; non-finite input is not rejected; the clock tolerance
argument is unused; and short windows divide by a full 60 seconds of unobserved
coverage. The baseline remains reproduced, but the analyzer is not yet validated
for arbitrary streams or partial windows.

The three-texture snapshot setting exists and is eligible for a separate A/B
trial. Claimed fps, CPU scheduling and shadow-pass savings remain unmeasured.
An 8 ms real-time declaration is not justified for a thread consuming about
22 ms, and the profiled 128 x 128 render target has not been established as a
shadow map. No scheduling change or pass suppression was adopted from these
recommendations.


## Existing GPU capture: scope of real-input evidence

A CPU-only inspector traced a byte-identical reference library through inferred
capture records to its function and pipeline. Re-running it found no references
to those objects in the decoded command streams. Its 18 synthetic parser tests
passed; they do not validate Apple's undocumented capture format. No verified
real-input replay of the target pipeline is available from this inspection.

The decoded image contains 14 compute dispatches using 11 other pipeline
objects. This is narrower than proving the absence of every compilation or
variant of the shader: some used libraries remain inside an undecoded packed
index/store representation. Function names and threadgroup size alone are
insufficient identifiers. Future replay would require proven dispatch identity,
resource state and dependencies, and reconstruction of argument-buffer handles
in the replay process. No new capture hook or production change was introduced.
