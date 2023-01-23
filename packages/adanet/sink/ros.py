from typing import Type, Dict

import cbor2
import rospy
from rospy.msg import AnyMsg

from .base import ISink
from ..networking.ros import ROS


class ROSSink(ISink):

    def __init__(self, name: str, size: int, *_, **kwargs):
        super(ROSSink, self).__init__(name=name, size=size)
        # make sure we are getting arguments
        if "arguments" not in kwargs:
            raise ValueError(f"Sink of type 'ROSSink' for channel '{name}' expected an 'arguments' object "
                             f"in the problem definition")
        self._arguments: Dict = kwargs["arguments"] or {}
        if "message_type" not in self._arguments:
            raise ValueError(f"Sinks of type 'ROSSink' for channel '{name}' expected an argument "
                             f"'message_type' in the problem definition")
        # register against the ROS network
        ROS.register()
        # get message type from arguments
        self.MsgType: Type[AnyMsg] = ROS.load_message_type(self._arguments["message_type"])

        # create publisher
        self._publisher = rospy.Publisher(self.topic, self.MsgType, queue_size=1)

    @property
    def topic(self) -> str:
        return self.name

    def recv(self, data: bytes):
        # deserialize char bytes into Python dict
        data: Dict = cbor2.loads(data)
        # convert Python dict to ROS message
        msg: AnyMsg = ROS.dict_to_message(data, self.MsgType)
        # send data out into the ROS network
        self._publisher.publish(msg)
