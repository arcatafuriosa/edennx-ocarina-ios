#!/usr/bin/env python3
"""Send a RomFS image to an iPhone app in fixed-size pieces (for images that `devicectl device copy to` cannot carry in one transfer).

Usage: push_romfs_parts.py <device UDID> <bundle ID> <RomFS.img> [--part-mib 1024] [--retries 5] [--workdir DIR]

Each piece goes to Documents/romfs.img.partNNN. The manifest Documents/romfs.parts (header
`DMROMFSPARTS1 size=<total> part=<bytes>`, then `<NNN> <sha256>` per piece) goes last. At its next start the app checks every piece
(size, SHA-256), writes it into Documents/romfs.img.assembling at its offset, deletes it, and renames the result to romfs.img; the build's
romfs.id identity check then decides whether the image is the one the build needs (main.m, romfs_assemble_parts).
Resumable: pieces already on the phone with the right size are skipped (a piece cut off halfway has the wrong size and is sent again).
"""
import argparse, hashlib, os, subprocess, sys, tempfile, time

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def sha256_file(path, chunk_size=8 << 20):
    """Hash a potentially multi-gigabyte file without reading it all into RAM."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()

def device_files(dev, bid):
    """{name: exact size in bytes} for Documents on the device (devicectl JSON output)."""
    import json
    with tempfile.NamedTemporaryFile(suffix=".json") as j:
        r = run(["xcrun", "devicectl", "device", "info", "files", "--device", dev, "--domain-type", "appDataContainer",
                 "--domain-identifier", bid, "--subdirectory", "Documents", "--json-output", j.name, "-q"])
        try: d = json.load(open(j.name))["result"]["files"]
        except Exception: return {}, r
    return {f["name"]: f["metadata"]["size"] for f in d}, r

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("device"); ap.add_argument("bundle"); ap.add_argument("image")
    ap.add_argument("--part-mib", type=int, default=1024); ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--workdir", default=None, help="folder for the piece being sent (default: next to the image)")
    ap.add_argument("--only", type=int, default=None, help="send only this piece index")
    a = ap.parse_args()
    part = a.part_mib << 20
    total = os.path.getsize(a.image); n = (total + part - 1) // part
    work = a.workdir or os.path.dirname(os.path.abspath(a.image))
    print(f"image {total} bytes, {n} pieces of {a.part_mib} MiB", flush=True)

    # SHA-256 of every piece (read once; one pass over the file)
    sums = []
    t0 = time.time()
    with open(a.image, "rb") as f:
        for i in range(n):
            h = hashlib.sha256(); left = min(part, total - i * part)
            while left:
                b = f.read(min(left, 8 << 20))
                if not b: sys.exit("[RED] image shorter than expected")
                h.update(b); left -= len(b)
            sums.append(h.hexdigest())
    print(f"hashed in {time.time()-t0:.0f}s", flush=True)

    have, _ = device_files(a.device, a.bundle)
    for i in range(n):
        if a.only is not None and i != a.only: continue
        name = f"romfs.img.part{i:03d}"; want = min(part, total - i * part)
        if have.get(name) == want:
            print(f"[{i+1}/{n}] {name} already on the phone", flush=True); continue
        tmp = os.path.join(work, name)
        if not (os.path.exists(tmp) and os.path.getsize(tmp) == want and sha256_file(tmp) == sums[i]):
            with open(a.image, "rb") as f, open(tmp, "wb") as o:
                f.seek(i * part); left = want
                while left:
                    b = f.read(min(left, 8 << 20)); o.write(b); left -= len(b)
        for attempt in range(1, a.retries + 1):
            t = time.time()
            r = run(["xcrun", "devicectl", "device", "copy", "to", "--device", a.device, "--domain-type", "appDataContainer",
                     "--domain-identifier", a.bundle, "--source", tmp, "--destination", f"Documents/{name}", "--timeout", "900", "-q"])
            got, _ = device_files(a.device, a.bundle)
            if r.returncode == 0 and got.get(name) == want:
                print(f"[{i+1}/{n}] {name} sent in {time.time()-t:.0f}s", flush=True); break
            print(f"[RED] {name} attempt {attempt} failed (rc={r.returncode}, on phone: {got.get(name)}): {(r.stderr or r.stdout)[-300:]}", flush=True)
            time.sleep(5)
        else:
            sys.exit(f"[RED] giving up on {name}; rerun to resume")
        if tmp != a.image: os.remove(tmp)

    if a.only is None:
        with tempfile.NamedTemporaryFile("w", suffix=".parts", delete=False) as m:
            m.write(f"DMROMFSPARTS1 size={total} part={part}\n")
            for i, s in enumerate(sums): m.write(f"{i:03d} {s}\n")
        r = run(["xcrun", "devicectl", "device", "copy", "to", "--device", a.device, "--domain-type", "appDataContainer",
                 "--domain-identifier", a.bundle, "--source", m.name, "--destination", "Documents/romfs.parts", "-q"])
        os.remove(m.name)
        if r.returncode: sys.exit(f"[RED] manifest not sent: {r.stderr}")
        print("manifest sent; start the app to assemble romfs.img", flush=True)

if __name__ == "__main__":
    main()
