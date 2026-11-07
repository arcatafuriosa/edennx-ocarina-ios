"""SPIR-V temporaries with a masked undefined value must not become MSL UB.

The logical result is independent of the temporary on the path that does not
store it. SPIR-V permits an undefined value there; reading an uninitialized
MSL bool is undefined behavior in the target language instead.
"""
import ast
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
CROSS = TOOLS / 'spirv_cross_bin/spirv-cross'
tree = ast.parse((TOOLS / 'dmsh_build.py').read_text())
XC = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
          and any(getattr(t, 'id', None) == 'XC' for t in n.targets))


def masked_temporary_spv():
    """out[i] = temp || odd(i); temp is stored only on the even path."""
    ids = {}
    def uid(name):
        if name not in ids: ids[name] = len(ids) + 1
        return ids[name]
    def op(code, *words): return [(len(words) + 1) << 16 | code, *words]
    def string(value):
        data = value.encode() + b'\0'; data += bytes(-len(data) % 4)
        return list(struct.unpack('<' + 'I' * (len(data) // 4), data))
    w = op(17, 1) + op(14, 0, 1)  # Shader; Logical / GLSL450 memory model
    w += op(15, 5, uid('main'), *string('main'), uid('gid'))
    w += op(16, uid('main'), 17, 32, 1, 1)
    w += op(71, uid('gid'), 11, 28)  # GlobalInvocationId
    w += op(71, uid('array'), 6, 4) + op(71, uid('struct'), 2)
    w += op(72, uid('struct'), 0, 35, 0)
    w += op(71, uid('out'), 34, 0) + op(71, uid('out'), 33, 0)
    w += op(19, uid('void')) + op(20, uid('bool')) + op(21, uid('uint'), 32, 0)
    w += op(23, uid('uvec3'), uid('uint'), 3)
    w += op(29, uid('array'), uid('uint')) + op(30, uid('struct'), uid('array'))
    w += op(32, uid('pin'), 1, uid('uvec3')) + op(32, uid('pout'), 12, uid('struct'))
    w += op(32, uid('pu'), 12, uid('uint')) + op(32, uid('pb'), 7, uid('bool'))
    w += op(33, uid('fn'), uid('void'))
    w += op(43, uid('uint'), uid('zero'), 0) + op(43, uid('uint'), uid('one'), 1)
    w += op(59, uid('pin'), uid('gid'), 1) + op(59, uid('pout'), uid('out'), 12)
    w += op(54, uid('void'), uid('main'), 0, uid('fn')) + op(248, uid('entry'))
    w += op(59, uid('pb'), uid('slot'), 7)  # uninitialized function temporary
    w += op(61, uid('uvec3'), uid('xyz'), uid('gid'))
    w += op(81, uid('uint'), uid('lane'), uid('xyz'), 0)
    w += op(199, uid('uint'), uid('bit'), uid('lane'), uid('one'))
    w += op(170, uid('bool'), uid('even'), uid('bit'), uid('zero'))
    w += op(247, uid('merge'), 0) + op(250, uid('even'), uid('yes'), uid('no'))
    w += op(248, uid('yes')) + op(170, uid('bool'), uid('value'), uid('lane'), uid('zero'))
    w += op(62, uid('slot'), uid('value')) + op(249, uid('merge'))
    w += op(248, uid('no')) + op(249, uid('merge'))
    w += op(248, uid('merge')) + op(61, uid('bool'), uid('temp'), uid('slot'))
    w += op(168, uid('bool'), uid('odd'), uid('even'))
    w += op(166, uid('bool'), uid('logical'), uid('temp'), uid('odd'))
    w += op(169, uid('uint'), uid('result'), uid('logical'), uid('one'), uid('zero'))
    w += op(65, uid('pu'), uid('ptr'), uid('out'), uid('zero'), uid('lane'))
    w += op(62, uid('ptr'), uid('result')) + op(253) + op(56)
    w = [0x07230203, 0x00010300, 0, len(ids) + 1, 0] + w
    return struct.pack('<' + 'I' * len(w), *w)


RUNNER = r'''
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <assert.h>
int main(int argc, const char **argv) { @autoreleasepool {
    assert(argc == 2); NSError *err = nil;
    NSString *s = [NSString stringWithContentsOfFile:@(argv[1]) encoding:NSUTF8StringEncoding error:&err]; assert(s);
    id<MTLDevice> d = MTLCreateSystemDefaultDevice(); assert(d);
    id<MTLLibrary> lib = [d newLibraryWithSource:s options:nil error:&err];
    if (!lib) { fprintf(stderr, "%s\n", err.description.UTF8String); return 1; }
    id<MTLFunction> fn = [lib newFunctionWithName:@"main0"]; assert(fn);
    id<MTLComputePipelineState> ps = [d newComputePipelineStateWithFunction:fn error:&err]; assert(ps);
    enum { N = 4096, ROUNDS = 16 };
    id<MTLBuffer> out = [d newBufferWithLength:N * sizeof(uint32_t) options:MTLResourceStorageModeShared];
    id<MTLArgumentEncoder> args = [fn newArgumentEncoderWithBufferIndex:0];
    id<MTLBuffer> ab = [d newBufferWithLength:args.encodedLength options:MTLResourceStorageModeShared];
    [args setArgumentBuffer:ab offset:0]; [args setBuffer:out offset:0 atIndex:0];
    id<MTLCommandQueue> q = [d newCommandQueue];
    for (unsigned r = 0; r < ROUNDS; r++) {
        memset(out.contents, 0xcc, out.length);
        id<MTLCommandBuffer> cb = [q commandBuffer]; id<MTLComputeCommandEncoder> e = [cb computeCommandEncoder];
        [e setComputePipelineState:ps]; [e setBuffer:ab offset:0 atIndex:0]; [e useResource:out usage:MTLResourceUsageWrite];
        [e dispatchThreads:MTLSizeMake(N,1,1) threadsPerThreadgroup:MTLSizeMake(32,1,1)];
        [e endEncoding]; [cb commit]; [cb waitUntilCompleted]; assert(cb.status == MTLCommandBufferStatusCompleted);
        uint32_t *v = out.contents;
        for (unsigned i = 0; i < N; i++) assert(v[i] == (uint32_t)(i == 0 || (i & 1)));
    }
    printf("masked temporary: %u results match the defined logical expression\n", N * ROUNDS);
}}
'''


@unittest.skipUnless(sys.platform == 'darwin' and shutil.which('xcrun') and CROSS.exists(), 'needs Metal and spirv-cross')
class InitializedTemporary(unittest.TestCase):
    def translate(self, work):
        spv, msl = work / 'masked.spv', work / 'masked.metal'
        spv.write_bytes(masked_temporary_spv())
        r = subprocess.run([str(CROSS), *XC, str(spv), '--output', str(msl)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return msl

    def test_masked_temporary_has_no_uninitialized_reads(self):
        with tempfile.TemporaryDirectory() as d:
            msl = self.translate(Path(d))
            r = subprocess.run(['xcrun', '-sdk', 'macosx', 'metal', '-fsyntax-only', '-O1',
                                '-Werror=uninitialized', str(msl)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    @unittest.skipUnless(os.environ.get('DMSH_TEST_GPU') == '1', 'set DMSH_TEST_GPU=1 for the Metal GPU test')
    def test_defined_results_match_reference_on_gpu(self):
        with tempfile.TemporaryDirectory() as d:
            work = Path(d); msl = self.translate(work)
            runner, exe = work / 'runner.m', work / 'runner'; runner.write_text(RUNNER)
            r = subprocess.run(['xcrun', 'clang', '-fobjc-arc', '-O2', '-framework', 'Foundation',
                                '-framework', 'Metal', str(runner), '-o', str(exe)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(exe), str(msl)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn('65536 results match', r.stdout)


if __name__ == '__main__': unittest.main()
