import json
from typing import Optional, List, Callable, Dict

import yaml
from pydantic import BaseModel, root_validator, validator
from pydantic.fields import ModelField

from adanet.networking.constants import NETWORK_TECHNOLOGIES
from adanet.utils import parse_bandwidth_str, parse_latency_str


class Link(BaseModel):

    class Config:
        extra = "allow"
        validate_all = True


    # name of the network interface at the OS level
    interface: str

    # shortcut to defining bandwidth and latency
    type: Optional[str] = None

    # network flow properties
    bandwidth: Optional[float] = None
    latency: Optional[float] = None

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
        print(v, values)
        # give precedence to explicit field value (if given)
        if v is not None:
            return parser(v)
        # populate field according to type (if given)
        if values["type"] is not None:
            t: str = values["type"].strip().lower()
            if t not in NETWORK_TECHNOLOGIES:
                raise ValueError(f"Technology '{t}' not recognized")
            tech: dict = NETWORK_TECHNOLOGIES[t]
            return parser(tech[field.name])

    # # noinspection PyMethodParameters
    # @root_validator
    # def _apply_network_interface_type(cls, values):
    #     """
    #     Populates the bandwidth and latency fields according to the given network interface
    #     technology type.
    #
    #     :param values:  dictionary of raw values being parsed
    #     :return:        dictionary of updated values
    #     """
    #     print(values)
    #     if values["type"] is not None:
    #         t: str = values["type"].strip().lower()
    #         if t not in NETWORK_TECHNOLOGIES:
    #             raise ValueError(f"Technology '{t}' not recognized")
    #         tech: dict = NETWORK_TECHNOLOGIES[t]
    #         for k, v in tech.items():
    #             if k not in values or values[k] is None:
    #                 values[k] = v
    #     print(values)
    #     return values


class ChannelQoS(BaseModel):
    latency: Optional[float] = None
    frequency: Optional[float] = None


class Channel(BaseModel):
    name: str
    priority: int = 0
    frequency: Optional[float] = None
    size: Optional[int] = None
    qos: Optional[ChannelQoS] = None


class Problem(BaseModel):
    links: Optional[List[Link]] = None
    channels: List[Channel]

    def as_json(self) -> str:
        return self.json(sort_keys=True, indent=4)

    def as_yaml(self) -> str:
        return yaml.safe_dump(json.loads(self.as_json()))
