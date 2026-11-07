"""Large RomFS transfer helpers must not load a whole piece into memory."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts import push_romfs_parts


class RomfsPartHash(unittest.TestCase):
    def test_hashes_a_file_larger_than_one_buffer(self):
        data = bytes(range(251)) * 9000
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "part.bin"
            path.write_bytes(data)
            self.assertEqual(push_romfs_parts.sha256_file(path, chunk_size=4096), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
