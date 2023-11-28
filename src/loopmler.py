import wave
import sys

import pyaudio

import numpy as np

CHUNK = 1024

#if len(sys.argv) < 2:
#    print(f'Plays a wave file. Usage: {sys.argv[0]} filename.wav')
#    sys.exit(-1)
file = '../see_the_sun.wav'
sample = []
sample_step = 0
note_on = True

with wave.open(file, 'rb') as wf:
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    #while len(data := wf.readframes(CHUNK)):
    data = wf.readframes(CHUNK)
    while len(data) > 0:
        #stream.write(data)
        data = wf.readframes(CHUNK)
        #sample.append(np.frombuffer(data))
        sample.append(data)

    while True:
        if note_on:
            sample_step += 1
            stream.write(sample[sample_step])


    stream.close()

    p.termainate


