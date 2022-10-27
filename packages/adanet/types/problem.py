from enum import Enum
from typing import Optional, List, Callable

from pydantic import validator

from adanet.networking.constants import NETWORK_TECHNOLOGIES
from adanet.types.misc import GenericModel
from adanet.utils import parse_bandwidth_str, parse_latency_str, parse_size_str


class LatencyPolicy(Enum):
    BEST_EFFORT = "best-effort"
    STRICT = "strict"


class Link(GenericModel):
    class Config:
        extra = "allow"
        validate_all = True

    # name of the network interface at the OS level
    interface: str

    # shortcut to defining bandwidth and latency
    type: Optional[str] = None

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
    priority: int = 0
    frequency: Optional[float] = None
    size: Optional[int] = None
    qos: Optional[ChannelQoS] = None

    def report(self) -> dict:
        return {
            "priority": self.priority,
            "frequency": self.frequency,
            "size": self.size,
            "qos": self.qos.report(),
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

    def report(self) -> dict:
        return {
            "links": {
                link.interface: link.report() for link in self.links
            },
            "channels": {
                channel.name.strip("/"): channel.report() for channel in self.channels
            }
        }
