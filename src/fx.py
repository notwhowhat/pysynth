from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voice import Voice

import random
from modulators import *
from fx import *

CHUNK: int = 1024

class Amp:
    def __init__(self, voice: Voice):
        self.voice: Voice = voice
        self.env: Envelope = Envelope(self.voice)
        self.mod: LFO = LFO(self.voice)
        
        # the gain isn't in dB, it's instead just a modifier.
        self.gain: float = 1000

    def amplify(self, sample: float) -> float:#chunk: np.ndarray):
        # TODO XXX: the envelope must react to the note.started and note.on for to
        # be able to turn off properly
        if self.env.on:
            if self.env != None:
                # use envelope first.
                sample *= self.env.senv(self.voice.note)
        '''
        else:
            # turns the note off when the trigger is removed.
            # shouldn't do this.
            if not self.voice.note.triggered:
                #print('stop time')
                sample *= 0
                if self.voice.note.started:
                    self.voice.note.on = False
                    # XXX: this is unsafe. what if something further in the chain needs to 
                    # use the frequency after this stage. make a function that checks for the 
                    # variable that will be made later, and set to delete the note soon.
                    self.voice.note.done = True

        if self.mod.on:
            if self.mod != None:
                # use modulator after.
                sample *= self.mod.get_osc(self.voice.note)
        '''

        #chunk *= self.gain
        sample *= self.gain
        return sample 

class Filter:
    def __init__(self, voice: Voice) -> None:
        self.type: str = 'low'
        self.cutoff_freq: float = random.randint(0, 20000)
        self.cutoff_freq = 20

        self.buffer0: int = 0
        self.buffer1: int = 0

        self.ctoff: float = random.randint(100, 200) #300.0

        self.sample_buffer: int = 0

    def get_filtered(self, chunk: np.ndarray):
        # the cutoff freq needs to be made to a dataindex for the fft
        cutoff_index = int(self.cutoff_freq * chunk.size / 44100)

        fft = np.fft.fft(chunk)

        for i in range(cutoff_index + 1, len(fft)):
            # sets it to 0 when it is past the cutoff
            fft[i] = 0

        # the inverse of it for to convert it back
        filtered = np.fft.ifft(fft)
        chunk = np.real(filtered)

    def get_mfiltered(self, chunk: np.ndarray) -> None:
        nchunk: list = []
        for i, e in enumerate(chunk):
            self.buffer0 += self.cutoff_freq * (e - self.buffer0) 
            self.buffer1 += self.cutoff_freq * (self.buffer0 - self.buffer1) 
            nchunk.append(self.buffer0)
        #chunk *= 1000
        chunk = nchunk
        print(chunk)

    def get_afiltered(self, chunk: np.ndarray) -> None:
        chunk += self.allpass(chunk)
        #chunk *= -1
        chunk *= 0.5


    def allpass(self, chunk: np.ndarray) -> np.ndarray:
        output: np.ndarray = np.zeros((CHUNK))

        for i in range(len(chunk)):
            # the coefficient is gotten per sample.
            ctan: float = np.tan(np.pi * self.ctoff / 44100)
            coefficient: float = (ctan - 1) / (ctan + 1)

            output[i] = coefficient * chunk[i] + self.sample_buffer
            self.sample_buffer = chunk[i] - coefficient * output[i]

        return output


