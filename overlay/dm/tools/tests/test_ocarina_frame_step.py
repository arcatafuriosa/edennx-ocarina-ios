"""Execute Ocarina's generated frame-controller stub on native arm64.

The controller must receive the host's interval and matching FPS, count elapsed
vsyncs, and leave the game alone when the override or step is unset.
"""
import importlib.util
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'dm/tools'))


class FrameController(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'darwin' and platform.machine() == 'arm64', 'native arm64 runner')
    def test_generated_stub_keeps_interval_fps_and_elapsed_time_together(self):
        path = REPO / 'dm/games/0400486024DEC000/patches.py'
        self.assertTrue(path.is_file(), 'Ocarina needs its own build-gated frame-controller hook')
        spec = importlib.util.spec_from_file_location('ocarina_patches', path)
        assert spec is not None and spec.loader is not None
        patches = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patches)
        self.assertEqual(set(patches.FRAME_STEP), {'e0f3ccfaf50065ae4ea01eb5aeb13b1a'})
        words, sites, writes = [], [], []
        ctx = SimpleNamespace(here=lambda: 0x5000 + 4 * len(words), emit=words.append,
                              site=lambda off, old: sites.append((off, old)), state=0x8000,
                              put=lambda *args: writes.append(args))
        patches.FRAME_STEP['e0f3ccfaf50065ae4ea01eb5aeb13b1a'](ctx)
        self.assertEqual(sites, [(0x3b4f074, 'e00314aa')])
        self.assertEqual(writes[0][0], sites[0][0])
        # Relocate the state page and the final return only; execute every
        # generated load, branch, arithmetic operation and store unchanged.
        asm = '.text\n.globl _run\n.p2align 2\n_run:\n stp x20,x30,[sp,#-16]!\n mov x20,x0\n adrp x16,_state@PAGE\n'
        asm += ''.join(f' .long {word:#x}\n' for word in words[1:-1])
        asm += ' ldp x20,x30,[sp],#16\n ret\n.data\n.p2align 14\n.globl _state\n_state:\n.space 64\n'
        c = '''#include <stdint.h>
#include <string.h>
extern unsigned char state[64]; extern void run(void *);
static int check(uint32_t target,uint32_t step,uint32_t interval,uint32_t fps,uint64_t elapsed){
 uint32_t cfg[32]; for(int i=0;i<32;i++)cfg[i]=0x77777777;
 memset(state,0,64);memcpy(state,&target,4);memcpy(state+0x20,&step,4);
 uint64_t before=91;memcpy(state+0x30,&before,8);run(cfg);
 uint64_t after;memcpy(&after,state+0x30,8);
 if(cfg[0x48/4]!=interval||cfg[0x58/4]!=fps||after!=elapsed)return 1;
 for(int i=0;i<32;i++)if(i!=0x48/4&&i!=0x58/4&&cfg[i]!=0x77777777)return 2;
 return 0;
}
int main(void){
 return check(0,2,0x77777777,0x77777777,91)||check(30,0,0x77777777,0x77777777,91)||
 check(30,2,2,30,93)||check(60,1,1,60,92)||check(60,3,3,20,94);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'stub.S').write_text(asm)
            (root / 'runner.c').write_text(c)
            subprocess.run(['clang', str(root / 'runner.c'), str(root / 'stub.S'), '-o', str(root / 'runner')], check=True, capture_output=True)
            result = subprocess.run([str(root / 'runner')], capture_output=True)
            self.assertEqual(result.returncode, 0, 'generated stub changed the interval, FPS, elapsed time or unrelated controller state incorrectly')


if __name__ == '__main__':
    unittest.main()
