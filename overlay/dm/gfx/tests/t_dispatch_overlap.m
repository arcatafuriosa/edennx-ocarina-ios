// A/B selection must actually alternate dispatch scheduling, while each real
// game barrier, copy and host dispatch continues to order dependent GPU work.
#define nvn_game_fps nvn_game_fps_mtl_default
#include "../nvn/nvn_mtl.m"
#undef nvn_game_fps
uint64_t g_t0_ns;
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s (line %d)\n", label, __LINE__); } } while (0)

static void encode(id<MTLComputePipelineState> ps, id<MTLBuffer> b, NSUInteger offset, int game) {
    id<MTL4ComputeCommandEncoder> e = dispatch_enc(game);
    enc_c_pso(e, ps); enc_c_args(e, b.gpuAddress + offset, 0);
    enc_c_dispatch(e, MTLSizeMake(16, 1, 1), MTLSizeMake(64, 1, 1));
}
static void ordering(void) {
    mtl_init();
    NSError *error = nil;
    id<MTLLibrary> lib = [g_dev newLibraryWithSource:@"#include <metal_stdlib>\nusing namespace metal;\n"
        "kernel void produce(device uint *p [[buffer(0)]], uint i [[thread_position_in_grid]]) { p[i] = i + 17; }\n"
        "kernel void consume(device uint *p [[buffer(0)]], uint i [[thread_position_in_grid]]) { p[1024+i] = p[i] + 1; }\n"
        options:nil error:&error];
    CHECK(lib != nil, "GPU fixture compiles"); if (!lib) { fprintf(stderr, "%s\n", error.description.UTF8String); return; }
    id<MTLComputePipelineState> producer = [g_dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"produce"] error:&error];
    id<MTLComputePipelineState> consumer = [g_dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"consume"] error:&error];
    id<MTLBuffer> b = [g_dev newBufferWithLength:16384 options:MTLResourceStorageModeShared];
    CHECK(producer && consumer && b, "GPU fixture pipelines and memory exist"); if (!producer || !consumer || !b) return;
    res_add(b);
    for (long phase = 0; phase < 2; phase++) {
        atomic_store(&g_ab_phase, phase); memset(b.contents, 0, b.length);
        mtl_sub_begin();
        encode(producer, b, 0, 1);
        uint64_t barriers = mtl_blit_barriers();
        encode(producer, b, 8192, 1);
        CHECK(mtl_blit_barriers() - barriers == (phase ? 0 : 1), "only enabled overlap removes the independent dispatch barrier");
        // Exercise the actual game's barrier command before a dependent reader.
        struct { op_hdr barrier; uint32_t bits, pad; op_hdr end; } commands = {
            {OP_BARRIER, 16}, NVN_BARRIER_ORDER_PRIMITIVES_BIT, 0, {OP_END, 8}};
        mtl_exec((const uint8_t *)&commands);
        barriers = mtl_blit_barriers(); encode(consumer, b, 0, 1);
        CHECK(mtl_blit_barriers() == barriers + 1, "a game barrier orders the dependent dispatch in both phases");
        barriers = mtl_blit_barriers(); encode(consumer, b, 8192, 0);
        CHECK(mtl_blit_barriers() == barriers + 1, "a host dispatch waits for earlier game dispatches");
        barriers = mtl_blit_barriers(); encode(producer, b, 8192, 1);
        CHECK(mtl_blit_barriers() == barriers + 1, "a game dispatch waits for a preceding host dispatch");
        barriers = mtl_blit_barriers();
        enc_b_copy_buffer(blit_buf(b.gpuAddress + 4096, b.gpuAddress + 8192, b.gpuAddress + 12288, b.gpuAddress + 16384), b, 4096, b, 12288, 4096);
        CHECK(mtl_blit_barriers() == barriers + 1, "a copy waits for all preceding dispatch writes");
        CHECK(mtl_wait(mtl_sub_commit(), 5000000000ull), "GPU work completes");
        CHECK(!mtl_last_commit_error(), "GPU work has no execution error");
        int correct = 1; const uint32_t *words = b.contents;
        for (unsigned i = 0; i < 1024; i++) correct &= words[1024 + i] == i + 18 && words[3072 + i] == i + 18;
        CHECK(correct, "dependent dispatch and copy read the producer's results");
    }
    res_remove(b);
}

int main(void) { @autoreleasepool {
    setenv("DM_AB", "120", 1);
    setenv("DM_NVN_DISPATCH_OVERLAP", "ab", 1);
    for (long phase = 0; phase < 4; phase++) {
        atomic_store(&g_ab_phase, phase);
        CHECK(dispatch_overlap() == (phase & 1), "dispatch overlap follows the current A/B phase");
    }
    int reported = 0;
    for (int i = 0; i < g_sw_n; i++) reported |= !strcmp(g_sw_name[i], "DM_NVN_DISPATCH_OVERLAP");
    CHECK(reported, "A/B results identify the dispatch-overlap configuration");
    ordering();
    printf("t_dispatch_overlap: %d checks, %d failed\n", checks, failed);
    return failed != 0;
} }
