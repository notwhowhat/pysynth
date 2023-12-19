import wave
import sys

import pyaudio

import numpy as np
from scipy.io.wavfile import read as sciread
import matplotlib.pyplot as plt

import time
import random

CHUNK = 1024

# only try files in mono, at 44100hz
file = '../see_the_sun.wav'
sampler_sample = []
sample_step = 0
note_on = True
play_list = []
notes = []

bass_freq = 466.16

#sample_duration_ns = 44100 / 1000000000
# at 44.1Khz one sample is 0.00002267573 seconds
sample_duration_ns = 1000000000 / 44100

bpm = 120
whole_note_duration = int(60000000000 / 120)

def chunkify(sound_array):
    chunks = []
    for i, e in enumerate(sound_array):
        val = e.astype(np.int16)
        if i % CHUNK == 0:
            chunks.append(np.array(()))

        chunks[-1] = np.append(chunks[-1], val)

    for chunk in chunks:
        chunk = chunk.astype(np.int16)
    return chunks

# time to add some envelopes, working with volume for to start with
# seperate envelopes for every part
# doesnt work if time in ns because giant operations

def get_factor(bass_freq, semitones):
    freq = (2 ** (semitones / 12)) * 440
    factor = bass_freq / freq
    return factor


def speedx(sound_array, factor):
    # create an array of the size of the sped array
    indices = np.round(np.arange(0, len(sound_array), factor))

    # makes the sped array fit into the other one
    indices = indices[indices < len(sound_array)].astype(int)
    return sound_array[indices.astype(int)]

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

        # which chunk it is on.
        self.chunk_step: int = 0
        self.freq = random.randint(220, 880)

class Voice:
    def __init__(self) -> None:
        # the voice's purpoouse is to be able to use instances for the notes.
        # handles and playes the note that is sent to it.
        self.amp: Amp = Amp(self)
        self.note: Note

    def get_chunk(self, current_time: int) -> np.ndarray:
        #current_time: int = time.time_ns()

        # now everything stops if the note does so too.
        # these features should be independent.
        if self.note.end > current_time:
            if self.note.start < current_time:
                # the note should be on if it has been started or is on.
                self.note.on = True

                if self.note.triggered:
                    # the note hasn't been triggered before
                    # then it should be marked.
                    self.note.started = True

                # the note is being held on.
                print('on ' + str(self))
                self.note.triggered = True
        else:
            print('off ' + str(self))
            self.note.triggered = False
        #return np.zeros((CHUNK))

        if self.note.on:
            # the envelope hasn't finnished, so the sound is on!

            # this triggering system is flawed, and turns off the note instead of
            # depending on the envelope.
            # the note is on

            start = self.note.chunk_step * CHUNK

            indexed_chunk = np.arange(start + 0, start + CHUNK)
            chunk = 1000 * np.sin(2.0 * np.pi / (44100 / self.note.freq) * indexed_chunk)

            # this makes a simple sloped env for every chunk.
            # next thing to do is to take a long array 
            # for to split it up in chunks now.

            # the envelope needs to be structured in a list
            # containing the envelope specific to the chunks

            # the release gets cut off beacuse of a flawed polyphony/note system
            # every note needs to be an object of a class instead of a list that's nested
            self.amp.amplify(chunk)
            
            self.note.chunk_step += 1
            return chunk
        #self.note.chunk_step += 1
        print('zeroead')
        # so basically, the note isn't "on"
        # check why that is.
        return np.zeros((CHUNK))

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

class Amp:
    def __init__(self, voice: Voice):
        self.voice: Voice = voice
        self.env: Envelope = Envelope(self.voice)
        self.mod: LFO = LFO(self.voice)
        
        # the gain isn't in dB, it's instead just a modifier.
        self.gain: float = 1

    def amplify(self, chunk: np.ndarray):
        if self.env.on:
            if self.env != None:
                # use envelope first.
                chunk *= self.env.get_env(self.voice.note)
        else:
            # turns the note off when the trigger is removed.
            # shouldn't do this.
            if not self.voice.note.triggered:
                #print('stop time')
                chunk *= 0
                if self.voice.note.started:
                    self.voice.note.on = False

        if self.mod.on:
            if self.mod != None:
                # use modulator after.
                chunk *= self.mod.get_osc(self.voice.note)

        chunk *= self.gain

class Envelope:
    def __init__(self, voice: Voice) -> None:
        # TODO: make the envelopes a bit better. The env doesn't need to
        # be "owned" by every instance. it only needs to be created once, because
        # it all is dependent on the notes instead.

        # the envelope shouldn't be owned by the Note, because
        # it is connected to a voice instead
        self.voice: Voice = voice
        self.on: bool = False

        self.ad_state: bool = False
        self.r_state: bool = False
        
        # env is unfortunatelly hardcoded :(
        self.ad_env: np.ndarray = np.linspace(0, 16, CHUNK * 100)
        self.r_env: np.ndarray = np.linspace(16, 0, CHUNK * 100)
        self.s_level: float = 8
        self.end: np.ndarray = np.zeros((CHUNK))

        self.ad_list: list = chunkify(self.ad_env)
        self.r_list: list = chunkify(self.r_env)

        self.last_note_step: int

    def trigger(self) -> None:
        # the envelope as just started going
        # reset the envelope too.
        self.ad_state = True
        self.r_state = False
        self.last_note_step = 0


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

    def get_ad(self, chunk_step: int) -> np.ndarray:
        self.last_note_step = chunk_step
        return self.ad_list[chunk_step]

    def get_s(self, chunk_step: int) -> np.ndarray:
        self.last_note_step = chunk_step
        return np.full((CHUNK), self.s_level)

    def get_r(self, chunk_step: int) -> np.ndarray:
        return self.r_list[chunk_step - self.last_note_step]

    def get_end(self) -> np.ndarray:
        return self.end


def new_note(start, end, source, freq=440):
    #start = time.time_ns()
    #end = start + 1000000000
    #source = 's' # from sampler
    chunk = 0
    freq = random.randint(0, 12) # tones instead of freq
    # index 6 is true, which is sound on
    notes.append([start, end, freq, source, chunk, True])


def play_notes():
    for i, note in enumerate(notes):
        #if note[1] > time.time_ns():
        if note.on:
            # note gets played
            factor = get_factor(bass_freq, note[2])
            stream.write(speedx(converted_wave, factor).astype(np.int16).tobytes())
        else:
            notes.remove(note)

def play(*chunks):
    master_chunk = np.zeros((CHUNK))
    for chunk in chunks:
       if len(chunk) == CHUNK:
        master_chunk += chunk
    stream.write(master_chunk.astype(np.int16).tobytes())

# this block is for the old reader.
'''
with wave.open(file, 'rb') as wf:
    sample_step = 0

    # reads all waves in binary
    raw_wave = wf.readframes(-1)

    #stream.write(raw_wave)

    #converted_wave = np.frombuffer(raw_wave, dtype=np.int16)

    #stream.write(speedx(converted_wave, 2).tobytes())

    #wav_chunks = chunkify(converted_wave * 0.4)
    #new_note()
    step = 0

    # this system works well if we know how long our notes will be. that isn't always the case.
    # then we need to have a system that just multiplies it iwth an empty chunk if the env is too big.
'''

p: pyaudio.PyAudio = pyaudio.PyAudio()

stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        output=True
)

current_time = time.time_ns()
# TODO: make the timings relative, because otherwise the load times of the notes
# do so that they don't get played, because the loading is 1.1+ seconds, when a note
# can be less than 1 sec.
# this does so that notes get triggered before they get played, sometimes a few seconds
# and then they don't get played.

for i in range(16):
    # add notes
    start = current_time + (10 * i * whole_note_duration)
    notes.append(Note(start, start + 10 * whole_note_duration, 'o'))

empty_chunk = np.zeros(CHUNK)
voice_count: int = 3

voices = []
for i in range(voice_count):
    voices.append(Voice())
    voices[i].note = notes[0]

#voice: Voice = Voice()
#voice.note = notes[0]

# there is something with the trigger, that does so that the voices can't play multiple notes
# simultaniously aswell as only being able to play notes before they have been zero, which
# leads to no audio output.

# investigate further on the trigger.
voices[0].note = notes[0]
voices[1].note = notes[1]
voices[2].note = notes[2]

# this is weird and crazy. i don't think that it is caused by the trigger, because it still exists
# when the amp is disabled, which does so that it has nothing to do with the trigger.


# TODO: just a sligt problem. the notes are always on from the beginning. should
# be simple to fix and related to the note.started variable which is recently added.




while notes:
    current_time = time.time_ns()
    chunks = []
    #for voice in voices:
    #    chunks.append(voice.get_chunk())
    #chunks.append(voices[0].get_chunk())
    #voices[0].note.chunk_step += 1 # the chunk param
    for v in voices:
        chunks.append(v.get_chunk(current_time))
    # sometimes a cycle only takes 0 ns, which is impossible.
    # my guess is that it doesn't get run. checked it, it's the only possible
    # way of it being 0 ns.
    # basically, it doesn't get played, and the chunks don't get generated.

    for e in []:

        '''
        # the worst voice handler ever!
        for note in notes:
            # TODO: must also check if note is done
            if note.start < current_time:
                # the note is active. therefore it needs a voice
                voice.note = note

                voice.note.chunk_step += 1 # the chunk param

                # TODO XXX: this shouldn't work. do so that the list copies itself 
                # instead of removing from the one that is iterating
                #notes.remove(note)
        '''

        # a problem is that both notes are on from the beginning.
        #voice.note.chunk_step += 1 # the chunk param



    #print(chunks)
    play(*chunks)

    #print('all time elapsed ' + str(timer - time.time_ns()))

stream.close()

p.terminate()

