import unittest

from mc_og_finder import build_charset, generate_names


class TestGenerator(unittest.TestCase):
    def test_build_charset_custom(self):
        self.assertEqual(build_charset("custom", "aabc"), "abc")

    def test_sequential_generation(self):
        names = list(
            generate_names(
                length=4,
                charset="ab",
                prefix="",
                suffix="",
                mode="sequential",
                max_candidates=5,
                words=[],
            )
        )
        self.assertEqual(names, ["aaaa", "aaab", "aaba", "aabb", "abaa"])

    def test_wordlist_generation(self):
        names = list(
            generate_names(
                length=4,
                charset="ab",
                prefix="",
                suffix="",
                mode="wordlist",
                max_candidates=10,
                words=["abc", "meme", "wolf", "hello"],
            )
        )
        self.assertEqual(names, ["meme", "wolf"])


if __name__ == "__main__":
    unittest.main()
