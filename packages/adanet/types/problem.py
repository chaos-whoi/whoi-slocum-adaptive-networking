import os
from enum import Enum
from ipaddress import IPv4Address
from typing import Optional, List, Callable, Dict, Iterable

from pydantic import validator

from adanet.networking.constants import NETWORK_TECHNOLOGIES
from adanet.types.misc import GenericModel
from adanet.utils import parse_bandwidth_str, parse_latency_str, parse_size_str


class LatencyPolicy(Enum):
    BEST_EFFORT = "best-effort"
    STRICT = "strict"


class ChannelKind(Enum):
    ROS = "ros"
    DISK = "disk"


class Link(GenericModel):
    class Config:
        extra = "allow"
        validate_all = True

    # name of the network interface at the OS level
    interface: str

    # shortcut to defining bandwidth and latency
    type: Optional[str] = None

    # optional static network configuration
    server: Optional[IPv4Address] = None

    # network flow properties
    bandwidth: Optional[float] = None
    latency: float = 0
    reliability: float = 1.0

    # the overall budget in Bytes that this link can use
    budget: Optional[float] = None

    # (internal use only)
    # - budget in Bytes that this link can use in each problem formulation
    capacity: Optional[float] = None

    # noinspection PyMethodParameters
    @validator("bandwidth", "latency")
    def _apply_network_interface_type(cls, v, values, field):
        """
        Populates the bandwidth and latency fields according to the given network interface
        technology type.

        :param values:  dictionary of raw values previously parsed
        :return:        dictionary of updated values
        """
        parser: Callable[[str], float] = {
            "bandwidth": parse_bandwidth_str,
            "latency": parse_latency_str,
        }[field.name]
        # give precedence to explicit field value (if given)
        if v is not None:
            if not isinstance(v, (int, float)):
                return parser(v)
            else:
                return float(v)
        # populate field according to type (if given)
        if values["type"] is not None:
            t: str = values["type"].strip().lower()
            if t not in NETWORK_TECHNOLOGIES:
                raise ValueError(f"Technology '{t}' not recognized")
            tech: dict = NETWORK_TECHNOLOGIES[t]
            return parser(tech[field.name])

    # noinspection PyMethodParameters
    @validator("budget", pre=True)
    def _parse_budget(cls, v):
        """
        Parses budget string into number of bytes.

        :return:   number of bytes
        """
        if v is not None:
            return parse_size_str(v)

    def report(self) -> dict:
        return {
            "bandwidth": self.bandwidth,
            "latency": self.latency,
            "budget": self.budget,
            "capacity": self.capacity,
        }


class ChannelQoS(GenericModel):
    queue_size: int = 1
    latency: Optional[float] = None
    frequency: Optional[float] = None
    latency_policy: LatencyPolicy = LatencyPolicy.BEST_EFFORT

    # noinspection PyMethodParameters
    @validator("latency", pre=True)
    def _parse_latency(cls, v):
        """
        Parses latency string into number of seconds.

        :return:   number of seconds
        """
        return parse_latency_str(v)

    def report(self) -> dict:
        return {
            "latency": self.latency,
            "frequency": self.frequency,
        }


class Channel(GenericModel):
    name: str
    kind: ChannelKind = ChannelKind.ROS
    arguments: Optional[Dict] = {}
    priority: int = 0
    frequency: Optional[float] = None
    size: Optional[int] = None
    qos: Optional[ChannelQoS] = None

    # (internal use only)
    # - packet stored in queue waiting to be bridged
    queue_length: int = 0

    def report(self) -> dict:
        return {
            "priority": self.priority,
            "frequency": self.frequency,
            "size": self.size,
            "qos": self.qos.report() if self.qos else None,
        }


class SimulatedChannel(GenericModel):
    name: str
    frequency: Optional[str] = None

    def report(self) -> dict:
        return {}


class SimulatedLink(GenericModel):
    interface: str
    bandwidth: Optional[str] = None
    latency: Optional[str] = None

    def report(self) -> dict:
        return {}


class Simulation(GenericModel):
    links: Optional[List[SimulatedLink]]
    channels: Optional[List[SimulatedChannel]]

    def report(self) -> dict:
        return {}


class Problem(GenericModel):
    links: Optional[List[Link]] = None
    channels: List[Channel]
    simulation: Optional[Simulation] = None
    name: str = "real"

    def categorize_channels(self, categories: Iterable[str]):
        old_channels: List[Channel] = self.channels
        new_channels: List[Channel] = []
        # iterate over the categories
        for category in categories:
            # iterate over the original channels
            for channel in old_channels:
                new_channel = channel.copy(deep=True)
                new_channel.name = os.path.join(category, channel.name.strip("/"))
                new_channels.append(new_channel)
        self.channels = new_channels
        # iterate over the simulated channels (if any)
        if self.simulation:
            old_channels: List[SimulatedChannel] = self.simulation.channels or []
            new_channels: List[SimulatedChannel] = []
            # iterate over the categories
            for category in categories:
                # iterate over the original channels
                for channel in old_channels:
                    new_channel = channel.copy(deep=True)
                    new_channel.name = os.path.join(category, channel.name.strip("/"))
                    new_channels.append(new_channel)
            self.simulation.channels = new_channels

    def report(self) -> dict:
        return {
            "links": {
                link.interface: link.report() for link in self.links
            },
            "channels": {
                channel.name.strip("/"): channel.report() for channel in self.channels
            }
        }
