from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voice import Voice

import numpy as np
from globals import *

class Osc:
    def __init__(self, voice: Voice):
        self.voice: Voice = voice

        self.freq: float = 440.0

        # types are: 'sin', 'square'
        self.type: str = 'square'

    def run(self, sample: float) -> float:
        if self.type == 'sin':
            sample: float = self.sin(sample)
        elif self.type == 'square':
            sample: float = self.square(sample)

        return sample

    def sin(self, sample: float) -> float:
        return np.sin(TAU / (SAMPLE_RATE / self.freq) * sample)

    def square(self, sample: float) -> float:
        sin = self.sin(sample)
        return np.ceil(sin)




