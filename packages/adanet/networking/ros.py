from threading import Semaphore
from typing import Type, Dict

import rospy
import rostopic

from adanet.types import Shuttable


class ROS:
    _lock: Semaphore = Semaphore()
    _registered: bool = False
    _shuttable: Shuttable = Shuttable()

    @classmethod
    def register(cls):
        with cls._lock:
            if cls._registered:
                return
            # initialize ROS node
            rospy.init_node('adanet_listener', disable_signals=True)
            # register for shutdown
            cls._shuttable.register_shutdown_callback(cls.shutdown)
            # mark as inited
            cls._registered = True

    @classmethod
    def shutdown(cls):
        rospy.signal_shutdown("User shutdown")

    @classmethod
    def get_message_type(cls, topic: str) -> Type[rospy.msg.AnyMsg]:
        msgtype, _, _ = rostopic.get_topic_type(topic)
        if msgtype is None:
            raise ValueError(f"Topic '{topic}' not found")
        assert msgtype.count("/") == 1
        catkin_pkg, message_name = msgtype.split("/")
        CatkinPkg = __import__(f"{catkin_pkg}.msg")
        return getattr(CatkinPkg.msg, message_name)

    @classmethod
    def message_to_dict(cls, msg: rospy.msg.AnyMsg) -> Dict:
        res: Dict = {}
        for k in msg.__slots__:
            v = getattr(msg, k)
            if hasattr(v, "__slots__"):
                v = cls.message_to_dict(v)
            res[k] = v
        return res
