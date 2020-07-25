import re
import logging
import json
from dstimer.common import unit_bh

logger = logging.getLogger("dstimer")


def intelli_single(format, actual):
    format = str(format).strip()
    # Format: x
    match = re.fullmatch(r"[0-9]+", format)
    if match is not None:
        val = int(format)
        return min(val, actual)
    # Format: *
    if format == "*":
        return actual
    # Format: >=x
    match = re.fullmatch(r">=([0-9]+)", format)
    if match is not None:
        requested = int(match.group(1))
        if actual >= requested:
            return actual
        else:
            return None
    # Format: =x
    match = re.fullmatch(r"=([0-9]+)", format)
    if match is not None:
        requested = int(match.group(1))
        if actual >= requested:
            return requested
        else:
            return None
    # Format: -x
    match = re.fullmatch(r"-([0-9]+)", format)
    if match is not None:
        reduce = int(match.group(1))
        return max(actual - reduce, 0)
    # Combined format: x, >= y or -x, >= y
    if "," in format:
        format = format.partition(",")
        left = intelli_single(format[0], actual)
        right = intelli_single(format[2], actual)
        if left is None or right is None:
            return None
        result = min(left, right)
        if intelli_single(format[0], result) is not None and intelli_single(format[2],
                                                                            result) is not None:
            return result
        else:
            return None
    # Error
    raise ValueError("Unknown format: {0}".format(format))


def intelli_all(format_obj, actual_obj):
    result = {}
    for unit in format_obj:
        x = intelli_single(format_obj[unit], actual_obj.get(unit, 0))
        if x is None:
            return None
        else:
            result[unit] = x
    return result


def intelli_train(action, actual_obj):
    if action["train"] != {}:
        # get all unit types used in train
        units = []
        for unit in action["units"]:
            units.append(unit)
        for counter in action["train"]:
            for unit in action["train"][counter]:
                if unit not in units:
                    units.append(unit)
        logger.info("units in train: " + json.dumps(units))
    #else:
    #    return intelli_all(action["units"], actual_obj)


def get_bh_all(format_obj):
    bh = 0
    for unit in format_obj:
        x = get_bh_single(format_obj[unit])
        if x is None:
            return None
        else:
            bh += x * unit_bh[unit]
    return bh


def get_bh_single(format):
    format = str(format)
    # Format: number
    match = re.fullmatch(r"[0-9]+", format)
    if match is not None:
        return int(format)
    # Format: *
    if format == "*":
        return None
    # Format: >=x
    match = re.fullmatch(r">=([0-9]+)", format)
    if match is not None:
        requested = int(match.group(1))
        return requested
    # Format: =x
    match = re.fullmatch(r"=([0-9]+)", format)
    if match is not None:
        requested = int(match.group(1))
        return requested
    # Format: -x
    match = re.fullmatch(r"-([0-9]+)", format)
    if match is not None:
        return None
    # Combined format: x, >= y or -x, >= y
    if "," in format:
        return None
    # Error
    raise ValueError("Unknown format: {0}".format(format))
