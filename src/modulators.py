from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voice import Voice

import numpy as np

from helpers import *

class LFO:
    def __init__(self, voice: Voice) -> None:
        # a basic lfo class to modulate other signals.
        # do not use as a standalone oscillator
        self.on: bool = False
        self.tau: float = 2.0 * np.pi
        self.rate: float = 2.0
        self.depth: int = 1

    def get_osc(self, note: Note):
        # the oscillations are not pregenerated, instead they are done in
        # "realtime" because they are offsett by chunks, for to reduce clicking
        indexed_chunk: np.ndarray = np.arange(note.chunk_step * CHUNK, 
                                              note.chunk_step * CHUNK + CHUNK)
        return self.depth * np.sin(self.tau / (44100 / self.rate) * indexed_chunk)

class Envelope:
    def __init__(self, voice: Voice) -> None:
        # TODO: make the envelopes a bit better. The env doesn't need to
        # be "owned" by every instance. it only needs to be created once, because
        # it all is dependent on the notes instead.

        # the envelope shouldn't be owned by the Note, because
        # it is connected to a voice instead
        self.voice: Voice = voice
        #self.on: bool = False
        self.on: bool = True

        self.ad_state: bool = False
        self.r_state: bool = False
        
        # env is unfortunatelly hardcoded :(
        self.ad_env: np.ndarray = np.linspace(0, 25, CHUNK * 50)
        self.r_env: np.ndarray = np.linspace(25, 0, CHUNK * 50)
        self.s_level: float = 25.0
        self.end: np.ndarray = np.zeros((CHUNK))

        self.ad_list: list = chunkify(self.ad_env)
        self.r_list: list = chunkify(self.r_env)

        self.last_note_step: int

    def trigger(self) -> None:
        # the envelope as just started going
        # reset the envelope too.

        # something isn't getting reset, which leads to the release stage not
        # being entered, because it 
        self.ad_state = True
        self.r_state = False
        self.last_note_step = 0

    def senv(self, note: Note) -> np.ndarray:
        # sample-wise instead of chunk based.
        self.note = note

        if self.note.sample_step == 0:
            # this isn't really accurate. remake so that it only goes throuhg when it actually does waht is should.
            self.trigger()

        # the release gets cut off beacuse of a flawed polyphony/note system
        # every note needs to be an object of a class instead of a list that's nested
        # it has some charming but buggy vibrato sound to it, will maybe investigate
        # in the future
        if self.note.sample_step < len(self.ad_env) - 1:
            # ad stage
            env = self.get_ad(note.sample_step, sample=True)
        elif self.note.triggered:
            # s stage
            # it only gets here when the note is on.
            env = self.get_s(self.last_note_step, sample=True)
        elif note.sample_step > len(self.ad_env) - self.last_note_step - 1:
            # r stage
            if note.sample_step >= len(self.ad_env) + len(self.r_env) - 2:
                # note is compleetly off, but it still exists
                env = self.get_end(sample=True)
            else:
                # release is on
                env = self.get_r(note.sample_step, sample=True)
                print('release yourself')
                # TODO: release is choppy??? FIX!!
        else:
            # note is compleetly off, but it still exists
            env = self.get_end(sample=True)

        return env




    def get_env(self, note: Note) -> np.ndarray:
        # just a basic update method
        self.note = note

        if self.note.chunk_step == 0:
            # if it is 0, it is a new note, so the env should be reset.
            self.trigger()

        # the release gets cut off beacuse of a flawed polyphony/note system
        # every note needs to be an object of a class instead of a list that's nested
        # it has some charming but buggy vibrato sound to it, will maybe investigate
        # in the future
        if self.note.chunk_step < len(self.ad_list) - 1:
            # ad stage
            env = self.get_ad(note.chunk_step)
        elif self.note.triggered:
            # s stage
            # it only gets here when the note is on.
            env = self.get_s(self.last_note_step)
        elif note.chunk_step > len(self.ad_list) - self.last_note_step - 1:
            # r stage
            if note.chunk_step >= len(self.ad_list) + len(self.r_list) - 2:
                # note is compleetly off, but it still exists
                env = self.get_end()
            else:
                # release is on
                env = self.get_r(note.chunk_step)
                print('release yourself')
        else:
            # note is compleetly off, but it still exists
            env = self.get_end()

        return env

    def get_ad(self, step: int, sample: bool=False) -> np.ndarray:
        self.last_note_step = step
        if sample:
            return self.ad_env[step]
        return self.ad_list[step]

    def get_s(self, step: int, sample: bool=False) -> np.ndarray:
        self.last_note_step = step
        if sample:
            return self.s_level
        return np.full((CHUNK), self.s_level)

    def get_r(self, step: int, sample: bool=False) -> np.ndarray:
        if sample:
            return self.r_env[step - self.last_note_step]
        return self.r_list[step - self.last_note_step]

    def get_end(self, sample: bool=False) -> np.ndarray:
        if sample:
            return 0
        return self.end


