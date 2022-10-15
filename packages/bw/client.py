#!/usr/bin/python3
import os
import time
from socket import *

BUFSIZE = 32
ip = os.environ.get("SERVER_HOST", "bw_server")
port = 5678

payload = b"x" * BUFSIZE


def human_size(value, suffix="B", precision=2):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(value) < 1024.0:
            # noinspection PyStringFormat
            return f"%3.{precision}f %s%s" % (value, unit, suffix)
        value /= 1024.0
    # noinspection PyStringFormat
    return f"%.{precision}f%s%s".format(value, "Yi", suffix)


def human_size_bits(value, suffix="b", precision=0):
    value *= 8
    for unit in ["", "k", "m", "g", "t", "p", "e", "z"]:
        if abs(value) < 1024.0:
            # noinspection PyStringFormat
            return f"%3.{precision}f %s%s" % (value, unit, suffix)
        value /= 1024.0
    # noinspection PyStringFormat
    return f"%.{precision}f%s%s".format(value, "Yi", suffix)


def client():
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((ip, port))
    s.settimeout(0.1)

    try:
        while True:
            t1 = time.time()
            total = 0
            while time.time() - t1 < 1:
                try:
                    total += s.send(payload)
                except timeout:
                    pass
            t2 = time.time()
            bandwidth = total / (t2 - t1)
            print("----------------------")
            # print(f"Bandwidth: {human_size(bandwidth)}/secs")
            print(f"Bandwidth: {human_size_bits(bandwidth)}ps")
    except KeyboardInterrupt:
        print("Exiting...")

    s.shutdown(1)


if __name__ == '__main__':
    client()
