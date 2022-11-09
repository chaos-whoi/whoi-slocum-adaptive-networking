from functools import partial
from threading import Semaphore
from typing import Optional, Dict, Type

from adanet.sink.base import ISink
from adanet.sink.disk import DiskSink
from adanet.sink.ros import ROSSink
from adanet.sink.simulated import SimulatedSink
from adanet.source.base import ISource
# - disk
from adanet.source.disk import DiskSource
# - ros
from adanet.source.ros import ROSSource
# sources and sinks
# - simulated
from adanet.source.simulated import SimulatedSource
from adanet.time import Clock
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.message import Message
from adanet.types.network import INetworkManager, ISwitchboard
from adanet.types.problem import Problem, Channel, ChannelKind
from adanet.types.solution import Solution, SolvedChannel


class Switchboard(Shuttable, ISwitchboard):

    def __init__(self, role: AgentRole, problem: Problem, simulation: bool = False):
        super(Switchboard, self).__init__()
        self._role = role
        self._problem: Problem = problem
        self._simulation: bool = simulation
        self._network_manager: Optional[INetworkManager] = None
        self._solution: Optional[Solution] = None
        self._channels: Dict[str, SolvedChannel] = {}
        self._sources: Dict[str, ISource] = {}
        self._sinks: Dict[str, ISink] = {}
        self._lock: Semaphore = Semaphore()

        # instantiate data sources
        if self._role is AgentRole.SOURCE:
            for channel in problem.channels:
                queue_size: int = channel.qos.queue_size if channel.qos else 1
                Source: Type[ISource] = self._source(channel)
                source: ISource = Source(name=channel.name,
                                         size=channel.size,
                                         frequency=channel.frequency,
                                         queue_size=queue_size,
                                         qos=channel.qos)
                source.register_callback(partial(self._send, channel.name))
                self._sources[channel.name] = source

        # instantiate data sinks
        if self._role is AgentRole.SINK:
            for channel in problem.channels:
                Sink: Type[ISink] = self._sink(channel)
                sink: ISink = Sink(name=channel.name,
                                   size=channel.size)
                self._sinks[channel.name] = sink

    @property
    def network_manager(self) -> INetworkManager:
        return self._network_manager

    @network_manager.setter
    def network_manager(self, network_manager: INetworkManager):
        self._network_manager = network_manager

    def source(self, name: str) -> ISource:
        return self._sources[name]

    def sink(self, name: str) -> ISink:
        return self._sinks[name]

    def start(self):
        # nothing to do
        pass

    def send(self, message: Message):
        with self._lock:
            # get channel solution
            solved_channel: Optional[SolvedChannel] = self._channels.get(message.channel, None)
            # make sure we have a solution for this channel
            if solved_channel is None:
                return
        # find next interface for this channel according to the current solution
        interface: Optional[str] = solved_channel.next()
        if interface is None:
            return
        # send data down to the network manager
        self._network_manager.send(interface, message)

    def recv(self, message: Message):
        # find channel's sink
        sink: Optional[ISink] = self._sinks.get(message.channel, None)
        if not sink:
            print(f"Received message for unknown channel '{message.channel}'")
            return
        # send data up to the sink
        sink.recv(message.payload)

    def _send(self, channel: str, data: bytes):
        # pack message
        message: Message = Message(channel, Clock.time(), data)
        # send message
        self.send(message)

    def update_solution(self, solution: Solution):
        with self._lock:
            self._solution = solution
            self._channels = {
                c.name: c for c in solution.assignments
            }
            # tell the sources what their solution frequency is
            for c in solution.assignments:
                self._sources[c.name].set_solution_frequency(c.frequency)
            # if we are simulating the problem, update the sources' frequency
            if self._simulation:
                # TODO: the idea here is that simulated sources can be throttled to the actual
                #       solution frequency given that the data is fake. Also, this would reduce
                #       the pressure on asyncio eventloop sleep
                # for c in solution.assignments:
                #     self._sources[c.name].update(frequency=c.frequency)
                # TODO:
                pass

    def _source(self, channel: Channel) -> Type[ISource]:
        # choose between simulated and real data sources
        if self._simulation:
            return SimulatedSource
        if channel.kind == ChannelKind.ROS.value:
            return ROSSource
        elif channel.kind == ChannelKind.DISK.value:
            return DiskSource
        else:
            raise ValueError(f"Unknown channel kind '{channel.kind}'")

    def _sink(self, channel: Channel) -> Type[ISink]:
        # choose between simulated and real data sinks
        if self._simulation:
            return SimulatedSink
        if channel.kind is ChannelKind.ROS:
            return ROSSink
        elif channel.kind is ChannelKind.DISK:
            return DiskSink
        else:
            raise ValueError(f"Unknown channel kind '{channel.kind}'")
