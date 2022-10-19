from typing import List

size_units: List[str] = ["", "k", "m", "g", "t", "p", "e", "z"]
time_units: List[str] = ["", "m", "n", "p"]


def _get_size_scale_factor(s: str):
    s = s.lower()
    if s not in size_units:
        raise ValueError(f"Unit '{s}' not recognized for bandwidth/size")
    exp: int = size_units.index(s)
    scale: float = 1024.0 ** exp
    return scale


def _get_time_scale_factor(s: str):
    if s not in time_units:
        raise ValueError(f"Unit '{s}' not recognized for time")
    exp: int = time_units.index(s)
    scale: float = 1.0 / (1000 ** exp)
    return scale


def parse_bandwidth_str(s: str) -> float:
    """
    Parses a human readable bandwidth string into
    the corresponding number of bytes per second "Bps".

    :param s: human-readable bandwidth string
    :return: corresponding number of bytes per second
    """
    s = s.strip()
    # we support only *bps and *Bps format
    if not s.endswith("bps") and not s.endswith("Bps"):
        raise ValueError(f"Bandwidth string '{s}' cannot be parsed")
    # compute b/B scaling factor
    f: float = 1.0 if s.endswith("Bps") else 8.0
    # parse string
    s = s.lower()
    for unit in reversed(size_units):
        u: str = f"{unit}bps"
        if s.endswith(u):
            print(s, u, len(u), s[0:-len(u)])
            v: float = float(s[0:-len(u)])
            return (v * _get_size_scale_factor(u[0:-len("bps")])) / f
    # in any other case, complain
    raise ValueError(f"Bandwidth string '{s}' cannot be parsed")


def parse_latency_str(s: str) -> float:
    """
    Parses a human readable latency string into
    the corresponding number of seconds.

    :param s: human-readable latency string
    :return: corresponding number of seconds
    """
    s = s.strip()
    # *s
    for unit in reversed(time_units):
        u: str = f"{unit}s"
        if s.endswith(u):
            v: float = float(s[0:-len(u)])
            return v * _get_time_scale_factor(u[0:-len("s")])
    # in any other case, complain
    raise ValueError(f"Latency string '{s}' cannot be parsed")
