import math

def distance(source_x, source_y, target_x, target_y):
    return math.sqrt(pow(target_x - source_x, 2) + pow(target_y - source_y, 2))

def speed(units, attack_or_support, stats):
    if not attack_or_support and units.get("knight", 0) > 0:
        return stats["knight"]
    slowest = 0
    for unit in units:
        if units[unit] > 0 and stats[unit] > slowest:
            slowest = stats[unit]
    return slowest

def runtime(speed, distance):
    return 60 * speed * distance
