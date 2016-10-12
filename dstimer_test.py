import unittest
from dstimer.send_action import intelli_single

class IntelliSingleTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(intelli_single("100", 101), 100)
        self.assertEqual(intelli_single("100", 100), 100)
        self.assertEqual(intelli_single("100", 99), 99)
        self.assertEqual(intelli_single("0", 10), 0)

    def test_star(self):
        self.assertEqual(intelli_single("*", 100), 100)
        self.assertEqual(intelli_single("*", 0), 0)

    def test_gte(self):
        self.assertEqual(intelli_single(">=100", 101), 101)
        self.assertEqual(intelli_single(">=100", 100), 100)
        self.assertEqual(intelli_single(">=100", 99), None)

    def test_eq(self):
        self.assertEqual(intelli_single("=100", 101), 100)
        self.assertEqual(intelli_single("=100", 100), 100)
        self.assertEqual(intelli_single("=100", 99), None)

    def test_minus(self):
        self.assertEqual(intelli_single("-50", 51), 1)
        self.assertEqual(intelli_single("-50", 50), 0)
        self.assertEqual(intelli_single("-50", 49), 0)

class IntelliAllTest(unittest.TestCase):
    def test_

if __name__ == "__main__":
    unittest.main()
