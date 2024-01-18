from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Callable

if TYPE_CHECKING:
    from voice import Voice

import numpy as np
import random
from globals import *
from modulators import *

class Osc:
    def __init__(self, voice: Voice):
        self.voice: Voice = voice
        self.mod: LFO = LFO(voice)
        self.mod_amount: float = 1

        #self.freq: float = 440.0

        #self.freq_mod: Mod = Mod('freq', self.freq)
        self.freq: Param = Param(440.0, self.mod)

        # types are: 'sin', 'square'
        self.type: str = 'square'

    def modulate(self, step: int) -> None:
        #self.freq *= 1 - (self.mod.get_osc(osc_step) * self.mod_amount)
        #self.freq *= self.mod.get_osc(osc_step) * self.mod_amount

        #mod = self.mod.generate(step)
        #self.freq *= mod 

        self.freq.modulate(step)





    def run(self, sample: float) -> float:
        self.modulate(sample)
        if self.type == 'sin':
            sample: float = self.sin(sample)
        elif self.type == 'square':
            sample: float = self.square(sample)

        return sample

    def sin(self, sample: float) -> float:
        return np.sin(TAU / (SAMPLE_RATE / self.freq.value) * sample)

    def square(self, sample: float) -> float:
        sin = self.sin(sample)
        return np.ceil(sin)




