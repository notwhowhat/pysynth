import random

from globals import *

class Note:
    def __init__(self, start: int, end: int, source: str, freq: float = 440.0) -> None:
        # only note data, no audio data :(
        # all of the times are in ns for performance.
        self.start: int = start
        self.end: int = end

        # the source is if it is from the sampler or the 
        # more "synth" like sine-wave generator
        # TODO: make the source into an oscillator obj.
        self.source: str = source
        self.freq: float = freq
        self.on: bool = False
        self.triggered: bool = False
        self.started: bool = False
        self.done: bool = False

        # which chunk it is on.
        self.chunk_step: int = 0
        self.sample_step: int = 0
        #self.freq = random.randint(330, 660)
        self.freq: float = 880.0

        # there will be four different states:
        # off, no key is held
        # on, when the key is held
        # offtr, when the key is turned off, or triggered
        # ontr, when the key is turned on, or triggered
        self.state: str = 'off'

    def set_state(self, time: int) -> None:
        '''
        # gets the state of the note. is used for envelopes...
        if self.end > time:
            if self.start < time:
                # the note is being held, but is this the first time?
                self.state = 'on'
        else:
            self.state = 'off'
        '''




        #'''
        if self.end > time:
            if self.start < time:
                # the note is being held, but is this the first time?
                if self.state != 'on' and self.state != 'ontr':
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


                #self.on = True
                # instead of having booleans for the states, i will instead use strings.
        #'''



