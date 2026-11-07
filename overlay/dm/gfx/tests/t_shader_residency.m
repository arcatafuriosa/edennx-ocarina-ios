// Shader keys read guest code on the CPU; hashing must not make it GPU resident.
#define nvn_game_fps nvn_game_fps_mtl_default
#include "../nvn/nvn_mtl.m"
#undef nvn_game_fps
#define g_ft g_ft_hle
#include "../nvn/hle_nvn.c"
#undef g_ft
uint64_t g_t0_ns;
void *front_metal_layer(void) { return NULL; }
module_t *module_of(const void *p) { (void)p; return NULL; }
module_t *g_mod; int g_nmod;
void svc_thread_dump(void) {}
uint64_t now_ns(void) { return bp_now(); }
static int checks, failed;
#define CHECK(c, label) do { checks++; if (!(c)) { failed++; fprintf(stderr, "FAIL: %s\n", label); } } while (0)
int main(void) { @autoreleasepool {
    mtl_init(); size_t size = getpagesize();
    void *mem = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    if (mem == MAP_FAILED) return 2;
    memset(mem, 0xa5, size);
    NVNmemoryPool pool = {0}; pool_builder_t builder = {.mem=mem, .size=size, .flags=0x24};
    CHECK(h_nvnMemoryPoolInitialize(&pool, (const NVNmemoryPoolBuilder *)&builder), "code pool initialized");
    int index = pool_find((uint64_t)mem, 16);
    CHECK(index >= 0 && !g_pools[index].res, "CPU-only code pool begins nonresident");
    uint8_t control[0x880] = {0}, direct[8], mapped[8]; uint32_t length = 16;
    memcpy(control + 0x704, &length, 4);
    NVNshaderData shader = {.data=(uint64_t)mem, .control=control};
    CHECK(keys_hash(&shader, 0, direct), "direct shader key computed");
    CHECK(keys_hash(&shader, 1, mapped) && !memcmp(direct, mapped, sizeof direct), "mapped shader key is unchanged");
    CHECK(!g_pools[index].res, "hashing code does not make its pool GPU resident");
    void *buffer; uint64_t offset;
    CHECK(mtl_addr((uint64_t)mem, 16, &buffer, &offset) && g_pools[index].res, "an actual GPU binding still makes the pool resident");
    h_nvnMemoryPoolFinalize(&pool); mtl_drain(); munmap(mem, size);
    printf("t_shader_residency: %d checks, %d failed\n", checks, failed); return failed != 0;
} }
