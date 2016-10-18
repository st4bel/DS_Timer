import re

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
        if intelli_single(format[0], result) is not None and intelli_single(format[2], result) is not None:
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
