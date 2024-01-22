from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voice import Voice

import random
from modulators import *
from fx import *

from globals import *

class Filter:
    def __init__(self, voice: Voice, cutoff: float, resonance: float) -> None:
        self.voice: Voice = voice

        #self.cutoff_freq: float = cutoff_freq
        #self.resonance: float = resonance

        self.cutoff: Param = Param(cutoff, None)
        self.resonance: Param = Param(resonance, None)



        self.params(self.cutoff, self.resonance)

    def params(self, cutoff_freq: float, resonance: float) -> None:
        # these parameters were orignally in init only, but if you need to change the
        # cutoff or res, all of the other variables also need to change.
        self.omega_c: float = TAU * self.cutoff.value / SAMPLE_RATE
        self.alpha: float = np.sin(self.omega_c) / (2.0 * self.resonance.value)

        self.b0: float = (1.0 - np.cos(self.omega_c)) / 2.0
        self.b1: float = 1.0 - np.cos(self.omega_c)
        self.b2: float = self.b0

        self.a0: float = 1.0 + self.alpha
        self.a1: float = -2.0 + np.cos(self.omega_c)
        self.a2: float = 1.0 - self.alpha

        self.x1: float = 0.0
        self.x2: float = 0.0
        self.y1: float = 0.0
        self.y2: float = 0.0

    def filter(self, sample: float) -> float:
        output = (self.b0 / self.a0) * sample + \
                 (self.b1 / self.a0) * self.x1 + (self.b2 / self.a0) * self.x2 - \
                 (self.a1 / self.a0) * self.y1 - (self.a2 / self.a0) * self.y2

        self.x2 = self.x1
        self.x1 = sample

        self.y2 = self.y1
        self.y1 = output

        return output

class Amp:
    def __init__(self, voice: Voice):
        self.voice: Voice = voice
        self.env: Envelope = Envelope(self.voice)
        self.mod: LFO = LFO(self.voice, 0.1, 10.0)
        
        # the gain isn't in dB, it's instead just a modifier.
        self.gain: float = 5000

    def amplify(self, sample: float) -> float:#chunk: np.ndarray):
        # TODO XXX: the envelope must react to the note.started and note.on for to
        # be able to turn off properly
        #'''
        if self.env.on:
            if self.env != None:
                # use envelope first.
                #sample *= self.env.senv(self.voice.note)
                sample *= self.env.output(self.voice.note)
                #sample *- self.env.generate(self.voice.note)
        #'''
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

class oFilter:
    def __init__(self, voice: Voice) -> None:
        self.voice: Voice = voice
        self.cutoff: float = 0.1
        self.resonance: float = 0 # 0 = high max, 1 = low max.

        self.sample_buffer: float = 0.0
        self.buffers: list = [0.0, 0.0]
        self.buffer0: float = 0.0
        self.buffer1: float = 0.0

        self.coefficient: float = self.coef()
        print(self.coefficient)

        # options are lp and hp
        self.type: str = 'lp'

        self.last_output: float = 0.0
        self.momentum: float = 0.0

    def filter(self, sample: float) -> float:
        # this is the main filtering method with choices of types.
        if self.type == 'lp':
            #for i in range(3):
            o0 = self.lpf(sample)
            sample = self.lpf(o0)
            #sample = self.rlpf(sample)

            output: float = sample

        return output

    def coef(self):
        # the filters need a coefficient for the cutoff.
        # the coefficient is a time constant, but it needs to be altered by the 
        # sample rate to work with the filtering as a coefficient.
        ctan: float = np.tan(np.pi * self.cutoff / SAMPLE_RATE)
        ctan /= 1.0 + ctan
        return ctan 

    def lpf(self, sample: float) -> float:
        # a state based filter
        self.last_output += (sample - self.last_output) * self.coefficient
        return self.last_output

    def rlpf(self, sample: float) -> float:
        # a resonant state based filter
        distance_to_go: float = sample - self.last_output
        self.momentum += distance_to_go * self.coefficient
        self.last_output += self.momentum + distance_to_go * self.resonance
        return self.last_output



class CFilter:
    def __init__(self, voice: Voice) -> None:
        self.type: str = 'low'
        self.cutoff_freq: float = random.randint(0, 20000)
        self.cutoff_freq = 20

        self.buffer0: int = 0
        self.buffer1: int = 0

        self.ctoff: float = random.randint(100, 200) #300.0

        self.sample_buffer: int = 0

        self.last_output: float = 0.0
        self.momentum: float = 0.0

    def lpf(self, sample: float) -> float:
        distance_to_go: float = sample - self.last_output
        self.last_output += distance_to_go * 0.125
        return self.last_output

    def rlpf(self, sample: float) -> float:
        distance_to_go: float = sample - self.last_output
        self.momentum += distance_to_go * 0.125
        self.last_output += self.momentum + distance_to_go * 0.125
        return self.last_output

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


