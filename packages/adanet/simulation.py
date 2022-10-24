from time import sleep
import math as mathlib
from threading import Thread, Semaphore
from typing import Dict, Union

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.time import Clock
from adanet.types import Shuttable
from adanet.types.problem import Problem, Channel, SimulatedChannel, SimulatedLink, Link


def step(period: Union[int, float], t: Union[int, float]):
    value: float = 1.0
    if (t // period) % 2 != 0:
        value = 0.0
    return value


class Simulator(Shuttable, Thread):

    def __init__(self, problem: Problem):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._problem: Problem = problem
        self._lock: Semaphore = Semaphore()
        # this is where we store the most up to date state of the links and channels
        # they will be applied to the actual problem every time the engine call step()
        self._link_update: Dict[str, Dict[str, float]] = {}
        self._channel_update: Dict[str, Dict[str, float]] = {}
        # this is where we store efficient maps between link interfaces (or channel names) and
        # their respective representative objects
        self._links_sim: Dict[str, SimulatedLink] = {
            l.interface: l for l in (self._problem.simulation.links if
                                     (self._problem.simulation is not None and
                                      self._problem.simulation.links is not None) else [])
        }
        self._channels_sim: Dict[str, SimulatedChannel] = {
            c.name: c for c in (self._problem.simulation.channels if
                                (self._problem.simulation is not None and
                                 self._problem.simulation.channels is not None) else [])
        }

    def step(self) -> Problem:
        with self._lock:
            # make a copy of the original problem (as at t=0)
            problem: Problem = self._problem.copy(deep=True)
            # apply the link updates
            for link in problem.links:
                if link.interface not in self._link_update:
                    continue
                link.__dict__.update(self._link_update[link.interface])
            # apply the channel updates
            for channel in problem.channels:
                if channel.name not in self._channel_update:
                    continue
                channel.__dict__.update(self._channel_update[channel.name])
        # return updated problem
        return problem

    def run(self):
        while not self.is_shutdown:
            with self._lock:
                # simulate links
                for link in self._problem.links:
                    if link.interface not in self._links_sim:
                        continue
                    # simulate link
                    simulation: SimulatedLink = self._links_sim[link.interface]
                    update: Dict[str, float] = self._update_link(link, simulation)
                    self._link_update[link.interface] = update
                # simulate channels
                for channel in self._problem.channels:
                    if channel.name not in self._channels_sim:
                        continue
                    # simulate channel
                    simulation: SimulatedChannel = self._channels_sim[channel.name]
                    update: Dict[str, float] = self._update_channel(channel, simulation)
                    self._channel_update[channel.name] = update
            # ---
            # we run 10 simulation steps every FORMULATE_PROBLEM_EVERY_SEC
            sleep(Clock.period(0.1 * FORMULATE_PROBLEM_EVERY_SEC))

    @staticmethod
    def _update_channel(channel: Channel, simulation: SimulatedChannel) -> Dict[str, float]:
        # NOTE: these are the variables available to the simulation scripts
        t: float = Clock.relative_time()
        c: Channel = channel
        math = mathlib
        # NOTE: -----------------------------------------------------------
        update: Dict[str, float] = {}
        # - simulate frequency
        if simulation.frequency:
            try:
                frequency: float = eval(simulation.frequency)
                update["frequency"] = frequency
            except Exception as e:
                print(f"ERROR: Could not evaluate simulation script '{simulation.frequency}' "
                      f"for channel '{channel.name}'. The exception generated is:\n{str(e)}")
        # return updated fields
        return update

    @staticmethod
    def _update_link(link: Link, simulation: SimulatedLink) -> Dict[str, float]:
        # NOTE: these are the variables available to the simulation scripts
        t: float = Clock.relative_time()
        l: Link = link
        math = mathlib
        # NOTE: -----------------------------------------------------------
        update: Dict[str, float] = {}
        # - simulate bandwidth
        if simulation.bandwidth:
            try:
                bandwidth: float = eval(simulation.bandwidth)
                update["bandwidth"] = bandwidth
            except Exception as e:
                print(f"ERROR: Could not evaluate simulation script '{simulation.bandwidth}' "
                      f"for link '{link.interface}'. The exception generated is:\n{str(e)}")
        # - simulate latency
        if simulation.latency:
            try:
                latency: float = eval(simulation.latency)
                update["latency"] = latency
            except Exception as e:
                print(f"ERROR: Could not evaluate simulation script '{simulation.latency}' "
                      f"for link '{link.interface}'. The exception generated is:\n{str(e)}")
        # return updated fields
        return update
