from threading import Semaphore
from typing import Type, Dict, Any

import rospy
import rostopic

from adanet.exceptions import ROSTopicNotFound
from adanet.types import Shuttable


class ROS:
    _lock: Semaphore = Semaphore()
    _registered: bool = False
    _shuttable: Shuttable = Shuttable()
    _cache: Dict[str, Type[rospy.msg.AnyMsg]] = {}

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
    def load_message_type(cls, msgtype: str) -> Type[rospy.msg.AnyMsg]:
        if msgtype in cls._cache:
            return cls._cache[msgtype]
        # load message from name
        assert msgtype.count("/") == 1
        catkin_pkg, message_name = msgtype.split("/")
        CatkinPkg = __import__(f"{catkin_pkg}.msg")
        MsgType: Type[rospy.msg.AnyMsg] = getattr(CatkinPkg.msg, message_name)
        # update cache
        cls._cache[msgtype] = MsgType
        # ---
        return MsgType

    @classmethod
    def get_message_type(cls, topic: str) -> Type[rospy.msg.AnyMsg]:
        msgtype, _, _ = rostopic.get_topic_type(topic)
        if msgtype is None:
            raise ROSTopicNotFound(f"Topic '{topic}' not found")
        return cls.load_message_type(msgtype)

    @classmethod
    def message_to_dict(cls, msg: rospy.msg.AnyMsg) -> Dict:
        res: Dict = {}
        for k in msg.__slots__:
            v = getattr(msg, k)
            if hasattr(v, "__slots__"):
                v = cls.message_to_dict(v)
            res[k] = v
        return res

    @classmethod
    def dict_to_message(cls, data: Dict, MsgType: Type[rospy.msg.AnyMsg]) -> rospy.msg.AnyMsg:
        fields: Dict = {}
        for i, k in enumerate(MsgType.__slots__):
            if k not in data:
                continue
            # get field value
            v: Any = data[k]
            # noinspection PyProtectedMember
            kt = MsgType._slot_types[i]
            if kt == "time":
                v = rospy.Time(**v)
            elif "/" in kt:
                FieldType: Type[rospy.msg.AnyMsg] = cls.load_message_type(kt)
                v = cls.dict_to_message(v, FieldType)
            # add field value
            fields[k] = v
        return MsgType(**fields)
