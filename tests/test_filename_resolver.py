import unittest
from filename_resolver import *


import tempfile
from pathlib import Path

class TestFilenameResolver(unittest.TestCase):
    def test_unique_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            (base / "file.txt").write_text("a")
            resolver = FileNameResolver(base)
            new_path = resolver.resolve_unique_path(base / "file.txt")
            self.assertEqual(new_path.name, "file_1.txt")
            new_path2 = resolver.resolve_unique_path(base / "file.txt")
            self.assertEqual(new_path2.name, "file_2.txt")

if __name__ == "__main__":
    unittest.main()
