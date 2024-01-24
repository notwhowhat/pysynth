import time
import sys
import pyaudio
import numpy as np

CNK: int = 1024
RATE: int = 44100
TAU: float = 2.0 * np.pi


p: pyaudio.PyAudio = pyaudio.PyAudio()
stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        output=True,
)

def play(stream, *cnk: np.ndarray) -> None:
    out: np.ndarray = np.zeros((CNK))
    for c in cnk:
        out = np.append(out, c)
    stream.write(out.astype(np.int16).tobytes())


def sin(step: int, freq: float) -> float:
    return np.sin(TAU / (RATE / freq) * step)

osc_step: int = 0

while True:
    out: np.ndarray = np.arange(osc_step, osc_step + CNK)
    
    for e in out:
        e = sin(osc_step, 440.0)

        osc_step += 1


    play(stream, out)
    




# last
stream.close()
p.terminate()



