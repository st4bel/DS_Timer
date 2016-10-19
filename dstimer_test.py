#!/usr/bin/env python3
import unittest
from dstimer.intelli_unit import intelli_single, intelli_all
from dstimer.import_action import speed

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

    def test_default_and_gte(self):
        self.assertEqual(intelli_single("100, >=50", 120), 100)
        self.assertEqual(intelli_single("100, >=50", 100), 100)
        self.assertEqual(intelli_single("100, >=50", 70), 70)
        self.assertEqual(intelli_single("100, >=50", 50), 50)
        self.assertEqual(intelli_single("100, >=50", 49), None)

    def test_default_and_minus(self):
        self.assertEqual(intelli_single("100, -10", 120), 100)
        self.assertEqual(intelli_single("100, -10", 105), 95)
        self.assertEqual(intelli_single("100, -10", 100), 90)
        self.assertEqual(intelli_single("100, -10", 90), 80)
        self.assertEqual(intelli_single("100, -10", 10), 0)

    def test_gte_and_minus(self):
        self.assertEqual(intelli_single(">=100, -10", 111), 101)
        self.assertEqual(intelli_single(">=100, -10", 110), 100)
        self.assertEqual(intelli_single(">=100, -10", 109), None)

    def test_eq_and_minus(self):
        self.assertEqual(intelli_single("=100, -10", 130), 100)
        self.assertEqual(intelli_single("=100, -10", 111), 100)
        self.assertEqual(intelli_single("=100, -10", 110), 100)
        self.assertEqual(intelli_single("=100, -10", 109), None)

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

class UnitSpeedTest(unittest.TestCase):
    def test_speed(self):
        stats = {"axe": 18, "militia": 0, "catapult": 30, "heavy": 11,
            "sword": 22, "ram": 30, "snob": 35, "knight": 10, "spear": 18,
            "spy": 9, "light": 10}

        self.assertEqual(speed(dict(spear=4, axe=2), "attack", stats), 18)
        self.assertEqual(speed(dict(spear=4, snob=0), "attack", stats), 18)
        self.assertEqual(speed(dict(spear=4, snob=1), "attack", stats), 35)
        self.assertEqual(speed(dict(knight=1, snob="=0"), "attack", stats), 10)
        self.assertEqual(speed(dict(light=">=20", snob="=0"), "attack", stats), 10)

if __name__ == "__main__":
    unittest.main()
