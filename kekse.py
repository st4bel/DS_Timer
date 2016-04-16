import re

FORMAT = re.compile(r"\[([a-zA-Z\.\-0-9]+)\|([a-zA-Z0-9%:]+)\|([a-zA-Z0-9]{8})\]")

def java_hash_code(str):
    """Recompute the hash given in an exported cookie. TODO This does not work as expected."""
    hash = 0
    if len(str) == 0:
        return hash
    for c in str:
        hash = ((hash << 5) - hash) + ord(c)
        # convert hash to int32
    return abs(hash)

def parse(str):
    """Parse an exported session cookie string from DS Kekse."""
    match = FORMAT.search(str)
    if match:
        return dict(domain=match.group(1), sid=match.group(2))
    else:
        return None
