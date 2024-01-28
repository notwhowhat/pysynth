from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voice import Voice

import numpy as np

SAMPLE_RATE: int = 44100
CHUNK: int = 1024
TAU: float = 2 * np.pi

voice_count: int = 16
osc_step: int = 0

params: dict = {
        'vol': 1.0,
        # amp env
        'atk': 44100,
        'dec': 22050,
        'sus': 1.0,
        'rel': 44100,
        # filter
        'cut': 20000.0,
        'res': 0.0,
}

def set_params(voice: Voice):
    voice.amp.gain = params.get('vol')
    voice.filter.cutoff


