import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import plagiarism_core as pc

SAMPLES = os.path.join(ROOT, "samples")


def read(name):
    with open(os.path.join(SAMPLES, name), encoding="utf-8") as f:
        return f.read()


class TestCore(unittest.TestCase):
    def test_normalize_positions(self):
        clean, pos = pc.normalize("Hi, You!")
        self.assertEqual(clean, "hiyou")
        self.assertEqual(pos, [0, 1, 4, 5, 6])

    def test_rolling_hash_equals_direct_hash(self):
        s, k = "abracadabra", 4
        rolled = pc.kgram_hashes(s, k)
        for i in range(len(s) - k + 1):
            self.assertEqual(rolled[i], pc.kgram_hashes(s[i:i + k], k)[0])

    def test_rk_and_naive_agree(self):
        a, b = pc.generate_pair(800, 0.3)
        na, _ = pc.normalize(a)
        nb, _ = pc.normalize(b)
        p1, _ = pc.find_matches_rk(na, nb, 15)
        p2, _ = pc.find_matches_naive(na, nb, 15)
        self.assertEqual(sorted(p1), sorted(p2))

    def test_small_modulus_creates_spurious_hits_but_same_result(self):
        a, b = pc.generate_pair(800, 0.3)
        na, _ = pc.normalize(a)
        nb, _ = pc.normalize(b)
        good, _ = pc.find_matches_rk(na, nb, 15)
        small, stats = pc.find_matches_rk(na, nb, 15, q=101)
        self.assertGreater(stats["spurious_hits"], 0)
        self.assertEqual(sorted(good), sorted(small))   # verification keeps it correct

    def test_identical_documents(self):
        t = read("original.txt")
        r = pc.analyze(t, t)
        self.assertAlmostEqual(r["coverage_a"], 100.0, places=3)
        self.assertEqual(len(r["blocks"]), 1)

    def test_unrelated_documents(self):
        r = pc.analyze(read("original.txt"), read("unrelated.txt"))
        self.assertLess(r["score"], 5)

    def test_partial_copy_detected(self):
        r = pc.analyze(read("original.txt"), read("copied_partial.txt"))
        self.assertGreater(r["coverage_a"], 30)
        self.assertLess(r["coverage_a"], 90)
        self.assertGreaterEqual(len(r["blocks"]), 2)

    def test_case_and_punctuation_do_not_hide_copying(self):
        a = "The quick brown fox jumps over the lazy dog near the river bank."
        b = "THE QUICK, BROWN FOX -- jumps over the lazy dog near the river bank!!"
        self.assertAlmostEqual(pc.analyze(a, b, k=10)["coverage_a"], 100.0, places=3)

    def test_too_short(self):
        self.assertTrue(pc.analyze("hi", "hello", k=20)["too_short"])

    def test_highlight_escapes_html(self):
        out = pc.highlight("a <b> c", [(2, 5)])
        self.assertIn("<mark>&lt;b&gt;</mark>", out)


if __name__ == "__main__":
    unittest.main()
