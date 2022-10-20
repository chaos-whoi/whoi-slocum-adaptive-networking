from adanet.utils import parse_bandwidth_str, parse_latency_str, parse_size_str


bw_units = ["", "k", "m", "g", "t", "p", "e", "z"]
lt_units = ["", "m", "n", "p"]
eps = 0.000001


def _assert_bandwidth(s: str, v: float):
    d: float = parse_bandwidth_str(s) - v
    assert d <= eps


def _assert_latency(s: str, v: float):
    d: float = parse_latency_str(s) - v
    assert d <= eps


def _assert_size(s: str, v: float):
    d: float = parse_size_str(s) - v
    assert d <= eps


def test_bandwidth_1():
    _assert_bandwidth("1bps", 1 / 8)


def test_bandwidth_2():
    _assert_bandwidth("1Bps", 1)


def test_bandwidth_all_units_bytes():
    for v in range(10):
        for exp, u in enumerate(bw_units):
            _assert_bandwidth(f"{v}{u}Bps", v * (1024 ** exp))


def test_bandwidth_all_units_bits():
    for v in range(10):
        for exp, u in enumerate(bw_units):
            _assert_bandwidth(f"{v}{u}bps", v * (1024 ** exp) / 8)


def test_latency_1():
    _assert_latency("1s", 1)


def test_latency_2():
    _assert_latency("1ms", 1 / 1000)


def test_latency_all_units():
    for v in range(10):
        for exp, u in enumerate(lt_units):
            _assert_latency(f"{v}{u}s", v / (1000 ** exp))


def test_size_1():
    _assert_size("1b", 1 / 8)


def test_size_2():
    _assert_size("1B", 1)


def test_size_all_units_bytes():
    for v in range(10):
        for exp, u in enumerate(bw_units):
            _assert_size(f"{v}{u}B", v * (1024 ** exp))


def test_size_all_units_bits():
    for v in range(10):
        for exp, u in enumerate(bw_units):
            _assert_size(f"{v}{u}b", v * (1024 ** exp) / 8)

