# Validation record — 2026-11-07

These results concern the local development tree from which the source delta was exported. They do not certify a new clone, every supported game, or an arbitrary iPhone/toolchain.

| Check | Evidence / limit |
|---|---|
| End-barrier probe | Six checks; command allocation in a 600-small-pass probe: 39,462,072 to 8,398,008 bytes. Not total game RAM or an equivalent fps gain. |
| Alias copy tests | 126 checks in direct and deferred modes. |
| Compatible image reuse | 332 checks in each exercised mode. |
| Mesh tests | 29 tests, including Mac/iOS Metal compilation; four bound cases failed before correction. A static census is not a measurement of runtime overruns. |
| Ampere tests | 79 tests. LDSM regression fails with the old translator and passes with the corrected one. |
| Local Apple GPU LDSM probe | 16,777,216 values, 64 rounds, including later shared-memory reuse, with no mismatch; Mac GPU evidence, not phone visual acceptance. |
| Undefined temporary tests | Old generation fails the uninitialized-warning compile check; new generation passes. GPU test checks 65,536 defined outputs. The old GPU output test also passed, so it alone is not evidence for the visual defect. GPU test is optional in CI. |
| Python lint | Existing 384-finding baseline respected with no added or stale entry. |
| Focused C lint | Main file retains the same 50 diagnostics as the pre-task snapshot. Global baseline deviations remain; not an all-green C check. |
| Full graphics suite | Attempted; build stops linking `t_gfx_suspend` because its stub lacks `dm_vi_frame_queued`. No successful full-suite result. |
| Multi-game regression | Not established: one local game build, no registered smoke route. |
| Previous complete shader chain | 42,845 primary keys retained, no lost earlier keys; nine known failures remain. |
| New initialization candidate | Full reconstruction running at export, not installed or accepted on the phone. |

The measured presentation run retained a two-texture ring and removed heavy readback/stack diagnostics. Comparing its pacing with an earlier run changes both instrumentation and launch conditions, so the entire difference cannot be attributed to buffering alone. White flashes still occurred.

Publication checks verify only the exported files, absence of disallowed material and patch applicability. They do not replace upstream regression testing or visual playtesting.
