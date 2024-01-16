from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voice import Voice

import random

from globals import *

class Note:
    def __init__(self, key: Key, start: int = None, end: int = None, sequencer=False) -> None:
        # only note data, no audio data :(
        # all of the times are in ns for performance.
        self.state_updater: bool = sequencer
        self.key: Key = key

        if start == None or end == None:
            # then the start times are irrelevant, so the values will be updated manually
            self.state_updater: bool = False
        self.start: int = start
        self.end: int = end

        self.freq: float = key.freq#freq
        self.prev_keystate: bool = self.key.on

        # which chunk it is on.
        self.chunk_step: int = 0
        self.sample_step: int = 0
        #self.freq = random.randint(330, 660)
        #self.freq: float = 880.0

        # there will be four different states:
        # off, no key is held
        # on, when the key is held
        # offtr, when the key is turned off, or triggered
        # ontr, when the key is turned on, or triggered
        self.state: str = 'off'
        self.distrubuted: bool = False

    def manual(self) -> None:
        if self.prev_keystate:
            if not self.key.on:
                self.state = 'offtr'
            else:
                self.state = 'on'
        else:
            if self.key.on:
                self.state = 'ontr'
            else:
                self.state = 'off'


        self.prev_keystate = self.key.on

    def set(self, time: int) -> None:

        #'''

        # when this is on, the state gets updated automaticaly using this method. otherwise it must be
        # done through the future note handeler for to have the note be turned off or not.
        if self.state_updater:
            if self.end > time:
                if self.start < time:
                    # the note is being held, but is this the first time?
                    if self.state == 'off' and self.state == 'offtr':
                        # well never has been or before!
                        # can not be triggering for multiple iterations.
                        self.state = 'ontr'

                    else:
                        # has been on for a trigger iteration
                        self.state = 'on'
            else:
                # not being held, and it has finished!
                if self.state == 'on':
                    # it was on last iterations so the first time it will be offtriggered
                    self.state = 'offtr'
                else:
                    self.state = 'off'

                    # instead of having booleans for the states, i will instead use strings.
        else:
            self.manual()

        if self.state == 'done':
            self = None

        #'''



