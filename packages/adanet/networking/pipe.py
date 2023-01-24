import time
from threading import Semaphore, Thread
from typing import Optional

import zmq as zmq

from adanet.constants import ZMQ_PUB_SERVER_PORT, ZMQ_SUB_SERVER_PORT, ZMQ_HEARTBEAT_EVERY_SEC, \
    INFTY
from adanet.time import Clock
from adanet.types import Shuttable


class Pipe(Shuttable, Thread):
    USER = b"0"
    SYSTEM = b"1"

    def __init__(self, pub_port: Optional[int] = None, sub_port: Optional[int] = None):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._inited: bool = False
        self._context: zmq.Context = zmq.Context()
        self._pub_port: int = pub_port or ZMQ_PUB_SERVER_PORT
        self._sub_port: int = sub_port or ZMQ_SUB_SERVER_PORT
        self._pub: zmq.Socket = self._context.socket(zmq.PUB)
        self._sub: zmq.Socket = self._context.socket(zmq.SUB)
        self._lock: Semaphore = Semaphore()
        # internal state
        self._last_heard: float = -INFTY

    @property
    def pub_port(self) -> int:
        return self._pub_port

    @property
    def sub_port(self) -> int:
        return self._sub_port

    @property
    def is_connected(self) -> bool:
        return (Clock.time() - self._last_heard) <= 2 * ZMQ_HEARTBEAT_EVERY_SEC

    @property
    def is_inited(self) -> bool:
        return self._inited

    def _configure(self):
        # avoids "waiting till ever" for a dead-peer on an already disconnected interconnect
        self._pub.setsockopt(zmq.LINGER, 0)
        # prevents buffering messages for a "later" delivery on not transmission-ready connections
        self._pub.setsockopt(zmq.IMMEDIATE, 1)
        # set high watermark
        self._pub.setsockopt(zmq.SNDHWM, 1)
        self._sub.setsockopt(zmq.RCVHWM, 1)
        # subscribe to everything
        self._sub.setsockopt(zmq.SUBSCRIBE, b"")
        # mark as inited
        self._inited = True

    def bind(self, base: str):
        # - PUB
        if self._pub_port == 0:
            address: str = f"tcp://{base}"
            print(f"Binding PUB to random port on {address}...")
            self._pub_port: int = self._pub.bind_to_random_port(address)
        else:
            address: str = f"tcp://{base}:{self._pub_port}"
            print(f"Binding PUB to {address}...")
            self._pub.bind(address)
        print(f"PUB Binded to {address}")
        # - SUB
        if self._sub_port == 0:
            address: str = f"tcp://{base}"
            print(f"Binding SUB to random port on {address}...")
            self._sub_port: int = self._sub.bind_to_random_port(address)
        else:
            address: str = f"tcp://{base}:{self._sub_port}"
            print(f"Binding SUB to {address}...")
            self._sub.bind(address)
        print(f"SUB binded to {address}")
        self._configure()

    def connect(self, server: str, pub_port: Optional[int] = None, sub_port: Optional[int] = None):
        # - PUB
        sub_port = sub_port or self._sub_port
        address: str = f"tcp://{server}:{sub_port}"
        print(f"Connecting PUB to {address}...")
        self._pub.connect(address)
        print(f"PUB connected to {address}")
        # - SUB
        pub_port = pub_port or self._pub_port
        address: str = f"tcp://{server}:{pub_port}"
        print(f"Connecting SUB to {address}...")
        self._sub.connect(address)
        print(f"SUB connected to {address}")
        self._configure()

    def reconnect(self, server: str, pub_port: Optional[int] = None, sub_port: Optional[int] = None):
        self.connect(server, pub_port, sub_port)

    def _send(self, data: bytes):
        with self._lock:
            self._pub.send_multipart((Pipe.SYSTEM, data))

    def send(self, data: bytes):
        with self._lock:
            self._pub.send_multipart((Pipe.USER, data))

    def recv(self) -> bytes:
        while not self.is_shutdown:
            parts = self._sub.recv_multipart()
            # validate number of parts
            if len(parts) != 2:
                continue
            # unpack parts
            level, data = parts
            # mark it as heard from
            self._last_heard = Clock.time()
            # system packets are hidden from the user
            if level == Pipe.SYSTEM:
                continue
            # user data
            return data

    def run(self) -> None:
        while not self.is_shutdown:
            self._send(b"x")
            time.sleep(Clock.period(ZMQ_HEARTBEAT_EVERY_SEC))
