import importlib.util
import pathlib
import tempfile
import unittest
from zipfile import ZipFile

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_skill_zip", ROOT / "dev/build_skill_zip.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackagingTests(unittest.TestCase):
    def test_build_single_skill_runtime_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            path = builder.build(pathlib.Path(td) / "skill.zip")
            with ZipFile(path) as z:
                files = z.namelist()
                self.assertEqual(len(files), 17)
                self.assertEqual(sum(n.endswith("/SKILL.md") for n in files), 1)
                self.assertNotIn("game-opportunity/scripts/example.py", files)
                self.assertTrue(z.testzip() is None)
                self.assertTrue(all(n.startswith("game-opportunity/") for n in files))


if __name__ == "__main__":
    unittest.main()
