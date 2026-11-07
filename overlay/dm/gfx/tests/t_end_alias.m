// End barriers must not duplicate the expensive alias flush kept on consumer barriers.
#include "../nvn/nvn_mtl.m"
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s\n", label); } } while (0)

static uint64_t command_bytes(id<MTLTexture> target, int production) {
    // Allocators retain their high-water mark: each control needs fresh storage.
    mtl_drain();
    for (int i = 0; i < g_alloc_n; i++) g_alloc4[i] = nil;
    g_alloc_n = 0; memset(g_alloc_fence, 0, sizeof g_alloc_fence);
    mtl_sub_begin();
    for (int i = 0; i < 600; i++) {
        MTL4RenderPassDescriptor *d = [MTL4RenderPassDescriptor new];
        d.colorAttachments[0].texture = target;
        d.colorAttachments[0].loadAction = MTLLoadActionClear;
        d.colorAttachments[0].storeAction = MTLStoreActionStore;
        d.colorAttachments[0].clearColor = MTLClearColorMake(.25, .5, .75, 1);
        id<MTL4RenderCommandEncoder> e = enc_r_begin(d);
        if (production) enc_r_end(e);
        else {
            // Identical consumer barrier; only the producer's alias flush differs.
            [e barrierAfterStages:MTLStageAll beforeQueueStages:MTLStageAll visibilityOptions:MTL4VisibilityOptionDevice];
            [e endEncoding];
        }
    }
    CHECK(mtl_wait(mtl_sub_commit(), 5000000000ull), "render submission completes");
    CHECK(!mtl_last_commit_error(), "render submission has no GPU error");
    return g_alloc4[g_alloc_cur].allocatedSize;
}
int main(void) { @autoreleasepool {
    setenv("DM_NVN_ENC_THREAD", "0", 1); mtl_init();
    MTLTextureDescriptor *d = [MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:8 height:8 mipmapped:NO];
    d.usage = MTLTextureUsageRenderTarget;
    id<MTLTexture> t = [g_dev newTextureWithDescriptor:d]; res_add(t);
    atomic_fetch_add(&g_big_n, 1);
    CHECK(resource_vis() & MTL4VisibilityOptionResourceAlias, "consumer barriers flush aliases");
    uint64_t control = command_bytes(t, 0), production = command_bytes(t, 1);
    printf("600 render passes: control %llu bytes, production %llu bytes\n", (unsigned long long)control, (unsigned long long)production);
    CHECK(production <= control + (2 << 20), "end barriers do not inflate command memory beyond the device-only control");
    atomic_fetch_sub(&g_big_n, 1); res_remove(t);
    printf("t_end_alias: %d checks, %d failed\n", checks, failed); return failed != 0;
} }
