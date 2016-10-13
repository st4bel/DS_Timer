#!/usr/bin/env python3
import unittest
from dstimer.intelli_unit import intelli_single, intelli_all

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
    def test_default(self):
        self.assertEqual(
            intelli_all(dict(sword=5, heavy=20, spy=1), dict(sword=20, heavy=10)),
            dict(sword=5, heavy=10, spy=0))

    def test_gte(self):
        self.assertEqual(
            intelli_all(dict(axe=">=50", heavy="10"), dict(axe=10)),
            None)

    def test_star(self):
        self.assertEqual(
            intelli_all(dict(spear="*", heavy="*"), dict(spear=20, heavy=30, light=50)),
            dict(spear=20, heavy=30))

    def test_empty_format(self):
        self.assertEqual(intelli_all(dict(), dict(spear=10, light=5)), dict())

    def test_empty_units(self):
        self.assertEqual(intelli_all(dict(spear=5, snob=1), dict()), dict(spear=0, snob=0))

if __name__ == "__main__":
    unittest.main()
