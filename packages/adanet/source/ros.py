from typing import Type, Dict

import cbor2
import rospy
from rospy.msg import AnyMsg

from .base import ISource
from ..networking.ros import ROS
from ..types.misc import FlowWatch


class ROSSource(ISource):

    def __init__(self, name: str, size: int, *args, **kwargs):
        super(ROSSource, self).__init__(name=name, size=size, *args, **kwargs)
        # register against the ROS network
        ROS.register()
        # get message type for topic
        MsgType: Type[AnyMsg] = ROS.get_message_type(self.topic)
        # create flowwatch object to monitor the topic's frequency
        self._flowwatch = FlowWatch()

        # pipe ROS messages into AdaNet
        def _callback(msg: AnyMsg):
            # convert ROS message to Python dict
            msg: Dict = ROS.message_to_dict(msg)
            # serialize Python dict into cbor bytes
            data: bytes = cbor2.dumps(msg)
            # send data out of the source and into the switchboard
            self._produce(data)
            # monitor frequency
            self._flowwatch.signal(len(data))
            self._frequency = self._flowwatch.frequency

        # subscribe
        rospy.Subscriber(self.topic, MsgType, _callback, queue_size=1)

    @property
    def topic(self) -> str:
        return self.name
