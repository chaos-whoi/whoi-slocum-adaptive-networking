import dataclasses

import cbor2


@dataclasses.dataclass
class Message:
    channel: str
    stamp: float
    payload: bytes

    def serialize(self) -> bytes:
        return cbor2.dumps({
            "channel": self.channel,
            "stamp": self.stamp,
            "payload": self.payload,
        })

    @staticmethod
    def deserialize(data: bytes) -> 'Message':
        return Message(**cbor2.loads(data))
