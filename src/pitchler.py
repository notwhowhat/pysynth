import wave
import sys

import pyaudio

import numpy as np
from scipy.io.wavfile import read as sciread
import matplotlib.pyplot as plt

CHUNK = 1024

#if len(sys.argv) < 2:
#    print(f'Plays a wave file. Usage: {sys.argv[0]} filename.wav')
#    sys.exit(-1)
file = '../see_the_sun.wav'
sampler_sample = []
sample_step = 0
note_on = True

def speedx(sound_array, factor):
    # create an array of the size of the sped array
    indices = np.round(np.arange(0, len(sound_array), factor))

    # makes the sped array fit into the other one
    indices = indices[indices < len(sound_array)].astype(int)
    return sound_array[indices.astype(int)]

with wave.open(file, 'rb') as wf:
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    output=True)

    unconverted_chunked = np.array(())
    converted_chunked = np.array(())

    unconverted = np.array(())
    converted = np.array(())

    hopefully_converted = np.array(())

    raw_wave = wf.readframes(-1)

    stream.write(raw_wave)

    converted_wave = np.frombuffer(raw_wave, dtype=np.int16)

    stream.write(speedx(converted_wave, 2).tobytes())

    # write last
    stream.write(converted_wave.tobytes())

    stream.close()

    p.terminate()


