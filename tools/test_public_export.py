"""Synthetic checks for the public export boundary; no real credentials or assets."""
import unittest
from check_public_export import problems


class ExportBoundary(unittest.TestCase):
    def test_source_is_allowed(self):
        self.assertEqual(problems('sample.py', b'print("synthetic")\n'), [])

    def test_game_file_is_rejected(self):
        self.assertIn('disallowed file type', problems('sample.nsp', b'synthetic'))

    def test_private_paths_are_rejected(self):
        data = b'/' + b'Users/' + b'example/work/file'
        self.assertIn('absolute personal/workstation path', problems('sample.txt', data))

    def test_device_id_is_rejected(self):
        data = b'0000' + b'0000-' + b'0' * 16
        self.assertIn('Apple device identifier', problems('sample.txt', data))

    def test_credential_is_rejected(self):
        data = b'gh' + b'p_' + b'x' * 36
        self.assertIn('GitHub credential', problems('sample.txt', data))

    def test_binary_is_rejected(self):
        self.assertIn('binary content', problems('sample.txt', bytes([0, 1, 2])))


if __name__ == '__main__':
    unittest.main()
