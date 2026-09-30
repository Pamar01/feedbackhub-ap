import unittest

from app.sentiment import analyze


class SentimentTests(unittest.TestCase):
    def test_positive(self):
        score, label = analyze("The app is great and very easy to use")
        self.assertEqual(label, "positive")
        self.assertGreater(score, 0)

    def test_negative(self):
        score, label = analyze("Terrible experience, the app is slow and buggy")
        self.assertEqual(label, "negative")
        self.assertLess(score, 0)

    def test_negation_flips_polarity(self):
        _, label = analyze("This is not good")
        self.assertEqual(label, "negative")
        _, label = analyze("This is not bad")
        self.assertEqual(label, "positive")

    def test_neutral_when_no_signal(self):
        score, label = analyze("I opened the page on Tuesday")
        self.assertEqual((score, label), (0.0, "neutral"))


if __name__ == "__main__":
    unittest.main()
