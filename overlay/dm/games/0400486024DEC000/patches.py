# Ocarina v131072: use the engine's native 30/60 fps controller so game time
# and presentation follow the same vsync interval. Adapted from OcarinaNX 2de238f.
from nso_asm import ADRP, B

# Platform workaround: the NDVE tensor network costs 65-94 ms per movie frame
# on the iPhone. Select the engine's existing plain movie player, which keeps
# the decoded 1920x1080 video and omits only the neural enhancement stage.
# Original bytes and module build ID are checked by the rewriter.
CUTS = {
    'e0f3ccfaf50065ae4ea01eb5aeb13b1a': [
        (0x3b5f524, '28010034', '09000014', 'movie player: use the decoded video without the NDVE tensor network'),
    ],
}

# v131072 main: the frame step (patch_nso.py "Frame step in whole vsyncs"). The game has its own frame-rate controller (main+0x3b4ef60, called once a frame with x20 = its
# config): from the measured frame time it picks a vsync interval between config +0x0 and +0x4 (with hysteresis, +0x50 / +0x54), stores it at +0x48 and fps = 60 / interval
# at +0x58, then at main+0x3b4f074 (where its paths meet) calls main+0x3b4f160, which hands +0x58 to setFrameRate (main+0x4dc0f0), and the framework's setInterval
# (main+0x346c5c0) with +0x48, which sets the window's present interval (main+0xf49970) and the framework's fps (+0xfc = 60 / interval). So 30 fps (interval 2) is the game's
# own mode, with its game time stepping by the interval. The stub at main+0x3b4f074 replaces the interval and fps with the host's step (state page +0x20, 1 = 60 fps, 2 = 30) while
# a target fps is set (state +0x0, the launcher's Frame rate / DM_FPS_TARGET; 0 = the game's own choice), and counts the vsyncs stepped (+0x30) for the host's speed check
def frame_step(ctx):
    here, emit, fs_site, fs_put, FS_STATE_OFF = ctx.here, ctx.emit, ctx.site, ctx.put, ctx.state
    site = 0x3b4f074
    fs_site(site, 'e00314aa')   # mov x0,x20
    start = here(); emit(ADRP(16, here(), FS_STATE_OFF))
    for w in (0xb9400211,   # ldr w17,[x16]           target fps (float bits; 0 = off)
              0x34000151,   # cbz w17,orig (+10)
              0xb9402211,   # ldr w17,[x16,#0x20]     step in vsyncs
              0x34000111,   # cbz w17,orig (+8)       not decided yet
              0xb9004a91,   # str w17,[x20,#0x48]     the controller's interval
              0x52800789,   # mov w9,#60
              0x1ad10929,   # udiv w9,w9,w17
              0xb9005a89,   # str w9,[x20,#0x58]      its fps, which setFrameRate takes
              0xf9401a09,   # ldr x9,[x16,#0x30]
              0x8b314129,   # add x9,x9,w17,uxtw
              0xf9001a09,   # str x9,[x16,#0x30]      vsyncs stepped
              0xaa1403e0):  # orig: mov x0,x20
        emit(w)
    emit(B(here(), site + 4))
    fs_put(site, [B(site, start)], "frame step: the frame-rate controller's interval and fps follow the host's vsyncs (state page target fps; 0 = the game's own choice)")

FRAME_STEP = {'e0f3ccfaf50065ae4ea01eb5aeb13b1a': frame_step}


BINDING = [
    {'what': 'movie player: decoded video without NDVE enhancement', 'now': 'build', 'goal': 'game', 'purpose': 'frame rate',
     'why': 'a platform workaround: the translated tensor network dominates the iPhone movie frame',
     'blocked': 'the tensor translation must become cheap enough before this workaround can be removed'},
    {'what': 'frame controller: interval and fps follow the host step', 'now': 'build', 'goal': 'game', 'purpose': 'frame rate',
     'why': 'the verified v131072 controller already supports whole-vsync intervals and steps game time by them',
     'blocked': 'frame-step stubs have no function-matched form yet'},
]

