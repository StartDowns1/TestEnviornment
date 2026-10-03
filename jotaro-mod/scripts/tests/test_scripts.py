"""Offline tests for the stdlib-only helper scripts. Run: python3 scripts/tests/test_scripts.py"""
import csv
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import summarize_procmon  # noqa: E402
import check_no_assets  # noqa: E402


class Procmon(unittest.TestCase):
    def test_fixture(self):
        with open(HERE / "procmon_fixture.txt", newline="") as fh:
            stats = summarize_procmon.summarize(csv.DictReader(fh), "data_win32", "NSUNS4.exe")
        body = stats[r"C:\G\data_win32\spc\1nrtbod1.xfbin"]
        self.assertEqual(body["attempts"], 3)
        self.assertTrue(body["opened"])
        self.assertEqual(body["results"]["NAME NOT FOUND"], 1)
        load = stats[r"C:\G\data_win32\spcload\1nrtspcload.xfbin"]
        self.assertFalse(load["opened"])
        self.assertNotIn(r"C:\G\data_win32\spc\other.xfbin", stats)  # other process filtered
        self.assertEqual(len(stats), 2)  # data1.cpk filtered by path


class Guard(unittest.TestCase):
    def test_rules(self):
        c = lambda p: check_no_assets.check(p, "/nonexistent")  # noqa: E731
        self.assertIsNone(c("jotaro-mod/scripts/x.py"))
        self.assertIsNone(c("jotaro-mod/out/rust/src/main.rs"))
        self.assertIsNone(c("jotaro-mod/out/phase3-work/a.py"))
        self.assertIsNotNone(c("jotaro-mod/out/phase3-work/sub/a.py"))
        self.assertIsNotNone(c("jotaro-mod/out/foo.txt"))
        self.assertIsNotNone(c("jotaro-mod/docs/a.png"))
        self.assertIsNotNone(c("x.xfbin"))
        self.assertIsNotNone(c("jotaro-mod/tools/a.exe"))


if __name__ == "__main__":
    unittest.main()
