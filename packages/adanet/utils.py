import re
from typing import List, Iterable, TypeVar, Iterator

size_units: List[str] = ["", "k", "m", "g", "t", "p", "e", "z"]
time_units: List[str] = ["", "m", "n", "p"]

T = TypeVar("T")


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
    s = s.strip().replace(" ", "")
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
    s = s.strip().replace(" ", "")
    # *s
    for unit in reversed(time_units):
        u: str = f"{unit}s"
        if s.endswith(u):
            v: float = float(s[0:-len(u)])
            return v * _get_time_scale_factor(u[0:-len("s")])
    # in any other case, complain
    raise ValueError(f"Latency string '{s}' cannot be parsed")


def parse_size_str(s: str) -> float:
    """
    Parses a human readable size string into
    the corresponding number of bytes.

    :param s: human-readable size string
    :return: corresponding number of bytes
    """
    s = s.strip().replace(" ", "")
    # we support only *b and *B format
    if not s.endswith("b") and not s.endswith("B"):
        raise ValueError(f"Size string '{s}' cannot be parsed")
    # compute b/B scaling factor
    f: float = 1.0 if s.endswith("B") else 8.0
    # parse string
    s = s.lower()
    for unit in reversed(size_units):
        u: str = f"{unit}b"
        if s.endswith(u):
            v: float = float(s[0:-len(u)])
            return (v * _get_size_scale_factor(u[0:-len("b")])) / f
    # in any other case, complain
    raise ValueError(f"Size string '{s}' cannot be parsed")


def infinite_iterator(iterable: Iterable[T]) -> Iterator[T]:
    while True:
        empty: bool = True
        for elem in iterable:
            empty = False
            yield elem
        if empty:
            return


def find_shortest_whole_repetitive_pattern(sequence: List[str]) -> List[str]:
    # convert sequence to string
    s: str = "|".join([""] + sequence)
    # find swrs (shortest whole repetitive substring)
    match: re.Match = re.match(r'(.+?)\1*$', s)
    # if an swrs cannot be found, return the full sequence
    if match is None:
        return sequence
    swrs: str = match.group(1)
    # convert swrs to sequence pattern
    return swrs.strip("|").split("|")
