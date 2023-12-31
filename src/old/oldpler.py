import wave
import sys

import pyaudio

import numpy as np
from scipy.io.wavfile import read as sciread
import matplotlib.pyplot as plt

import time
import random

CHUNK = 1024

#if len(sys.argv) < 2:
#    print(f'Plays a wave file. Usage: {sys.argv[0]} filename.wav')
#    sys.exit(-1)

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
envelopes = [
        np.linspace(0, 2, 44100),
        np.linspace(2, 1, 44100),
        np.full((44100,), 1),
        np.linspace(1, 0, 44100),
]

envelope = np.array(())
for e in envelopes:
    envelope = np.append(envelope, e)

envelope_chunks = chunkify(envelope)
#print(len(envelope))
#print('i')
#for c in envelope_chunks:
    #print(len(c))

fade_env = np.linspace(0, 2, 44100)
fade_chunks = chunkify(fade_env)

#plt.plot(envelope)
#plt.show()

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

#def new_note(freq=440):
#    start = time.time_ns()
#    end = start + 1000000000
#    source = 's' # from sampler
#    chunk = 0
#    notes.append([start, end, freq, source, chunk])

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
        self.on: bool = True
        self.triggered = False

        # which chunk it is on.
        self.chunk_step: int = 0

class Voice:
    def __init__(self):
        # the voice's purpoouse is to be able to use instances for the notes.
        # handles and playes the note that is sent to it.
        self.amp = Amp(self)
        self.note: Note

    def get_chunk(self):
        current_time: int = time.time_ns()
        #print(self.note.start - current_time)

        # now everything stops if the note does so too.
        # these features should be independent.
        if self.note.end > current_time:
            if self.note.start < current_time:
                # the note is being held on.
                print('on')
                self.note.triggered = True
        else:
            print('off')
            self.note.triggered = False
        #return np.zeros((CHUNK))

        if self.note.on:
            # the envelope hasn't finnished, so the sound is on!

            # this triggering system is flawed, and turns off the note instead of
            # depending on the envelope.
            # the note is on

            start = self.note.chunk_step * CHUNK

            indexed_chunk = np.arange(start + 0, start + CHUNK)
            chunk = 1000 * np.sin(2.0 * np.pi / (44100 / 440) * indexed_chunk)

            # this makes a simple sloped env for every chunk.
            # next thing to do is to take a long array 
            # for to split it up in chunks now.

            # the envelope needs to be structured in a list
            # containing the envelope specific to the chunks

            # the release gets cut off beacuse of a flawed polyphony/note system
            # every note needs to be an object of a class instead of a list that's nested
            self.amp.amplify(chunk)
            
            return chunk
        return np.zeros((CHUNK))

class LFO:
    def __init__(self, voice: Voice) -> None:
        # a basic lfo class to modulate other signals.
        # do not use as a standalone oscillator
        self.on: bool = True
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
        #self.modulator: Envelope = None
        self.env: Envelope = Envelope(self.voice)
        #self.env_on: bool = False
        self.mod: LFO = LFO(self.voice)
        #self.mod_on: bool = True
        
        # the gain isn't in dB, it's instead just a modifier.
        self.gain: float = 1

    def amplify(self, chunk: np.ndarray):
        if self.env.on:
            if self.env != None:
                # use envelope first.
                chunk *= self.env.get_env(self.voice.note)
        else:
            # turns the note off when the trigger is removed.
            if not self.voice.note.triggered:
                #print('stop time')
                chunk *= 0
                self.voice.note.on = False

        if self.mod.on:
            if self.mod != None:
                # use modulator after.
                chunk *= self.mod.get_osc(self.voice.note)

        chunk *= self.gain

class Envelope:
    def __init__(self, voice: Voice) -> None:
        # the envelope shouldn't be owned by the Note, because
        # it is connected to a voice instead
        self.voice: Voice = voice
        self.on: bool = True

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
    master_chunk = np.array(())
    for chunk in chunks:
       master_chunk = np.append(master_chunk, chunk) 
    stream.write(master_chunk.astype(np.int16).tobytes())

with wave.open(file, 'rb') as wf:
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    output=True)

    sample_step = 0

    # reads all waves in binary
    raw_wave = wf.readframes(-1)

    #stream.write(raw_wave)

    converted_wave = np.frombuffer(raw_wave, dtype=np.int16)

    #stream.write(speedx(converted_wave, 2).tobytes())

    wav_chunks = chunkify(converted_wave * 0.4)
    #new_note()
    step = 0

    # about 2 ms from here
    current_time = time.time_ns()
    # TODO: Make the timings relative, because otherwise the load times of the notes
    # do so that they don't get played, because the loading is 1.1+ seconds, when a note
    # can be less than 1 sec.
    for i in range(16):
        # add notes
        #start = current_time + (i * 1000000000 * 2)
        #new_note(start, start + 1000000000 * 2, 's')

        # uncomment under
        start = current_time + (i * whole_note_duration)
        #new_note(start, start + whole_note_duration, 's')
        #new_note(start, start + whole_note_duration, 'o')
        notes.append(Note(start, start + 10 * whole_note_duration, 'o'))

    melody_start = time.time_ns()
    #new_note(melody_start, melody_start + whole_note_duration, 's'),
    #new_note(melody_start + (whole_note_duration * 2), melody_start + (whole_note_duration * 3), 's'),
    #new_note(melody_start + (whole_note_duration * 4), melody_start + (whole_note_duration * 5), 's'),
    #new_note(melody_start + (whole_note_duration * 6), melody_start + (whole_note_duration * 7), 's'),

    timer = current_time
    qenv = np.linspace(0, 2, CHUNK)

    # this system works well if we know how long our notes will be. that isn't always the case.
    # then we need to have a system that just multiplies it iwth an empty chunk if the env is too big.
    lenvs = []
    renvs = []
    lenv = np.linspace(0, 2, 25 * CHUNK)
    aenv = np.linspace(0, 16, 10 * CHUNK)
    denv = np.linspace(16, 8, 10 * CHUNK)

    renv = np.linspace(8, 0, 50 * CHUNK)

    adenv = np.append(aenv, denv)
    for i in range(20):
        #lenvs.append(lenv[i * CHUNK : i * CHUNK + CHUNK]) 
        lenvs.append(adenv[i * CHUNK : i * CHUNK + CHUNK]) 
    for i in range(50):
        renvs.append(renv[i * CHUNK : i * CHUNK + CHUNK]) 
    # to 
    # to here

    '''
    flenv = np.array(())
    for e in lenvs:
        flenv = np.append(flenv, e)
    plt.plot(flenv)
    plt.show()

    print(len(notes))
    print(notes)
    '''


    #while True:
    empty_chunk = np.zeros(CHUNK)

    voice: Voice = Voice()
    voice.note = notes[0]

    while notes:
        chunks = []
        print(voice.get_chunk())
        current_time = time.time_ns()
        chunks.append(voice.get_chunk().astype(np.int16))
        #osc = osc.astype(np.int16)
        #plt.plot(osc)
        #plt.show()
        #print(note[4])
        #chunks.append(osc)
        #print('play')

        #plt.plot(osc)
        #plt.show()

        voice.note.chunk_step += 1 # the chunk param
        print(current_time - time.time_ns())

        for note in notes: 
            current_time = time.time_ns()

            # get which sample
            #te = current_time - note[2]
            #point = te * (1/44100)
            #chunk_nr = int((point % CHUNK) / CHUNK)
            #print(point)
            #elapsed_note_time = current_time - note[2] # start_time
            #samples_played = elapsed_note_time / (sample_duration_ns * CHUNK)
            #chunk_nr = int(samples_played % CHUNK)

            #chunk_nr = int((current_time - note[2]) / sample_duration_ns) # start time
            #print(chunk_nr)
            #chunk_nr = 10

            # next thing to add:
            # envelopes for the chunks

            # these first 2 checks see if the note is playing or not
            '''
            if note.end > time.time_ns():#current_time:
                if note.start < time.time_ns():
                    if note.source == 's': # noise source is sample so step the chunk param
                        # using this implementation the list storing all note data wont be readonly
                        # but python still probably opens it for a write still. well it is probably
                        # quicker to use some more ram than semi-complex math on at least 10^12 numbers

                        # the samples are now pitched
                        if note.chunk_step < len(wav_chunks): # what chunk
                            factor = get_factor(466.164, note.freq) # see the sun is in b flat
                            # speeds induvidual chunks. might not be grate, but it works for now
                            chunks.append(speedx(
                                wav_chunks[note.chunk_step],
                                factor
                            ))

                            note.chunk_step += 1 # the chunk param
                            print(note)

                    if note.source == 'o': # noise source is osc
                        #osc = 1 * np.sin(2.0 * np.pi / (44100 / 440) * empty_chunk)

                        start = note.chunk_step * CHUNK

                        #indexed_chunk = np.arange(note[4] + 0, note[4] + CHUNK)
                        indexed_chunk = np.arange(start + 0, start + CHUNK)
                        # osc -> oscillation
                        osc = 1000 * np.sin(2.0 * np.pi / (44100 / 440) * indexed_chunk)

                        # this makes a simple sloped env for every chunk.
                        #osc = osc * qenv

                        # next thing to do is to take a long array 
                        # for to split it up in chunks now.

                        # the envelope needs to be structured in a list
                        # containing the envelope specific to the chunks

                        # the release gets cut off beacuse of a flawed polyphony/note system
                        # every note needs to be an object of a class instead of a list that's nested
                        if note.chunk_step < len(lenvs) - 1:
                            lenv_stage = True
                            renv_stage = False
                        elif note.chunk_step > len(lenvs) - len(renvs) - 1:
                            lenv_stage = False
                            renv_stage = True 
                        else:
                            #print('off early')
                            lenv_stage = False
                            renv_stage = False

                        if lenv_stage:
                            # the ad env is on!
                            print('ad')

                            # well time to take a brake for today.
                            # for to accomplish that i think i need a note list/dict, where all of the notes
                            # are stored, even after they have been triggered.
                            osc = osc * lenvs[note.chunk_step]

                            # note[4] doesn't get reset, but the renv needs to start at 0
                            last_note_step = note.chunk_step
                        elif renv_stage:
                            print('release yourself')
                            osc = osc * renvs[note.chunk_step - last_note_step]
                        else:
                            # none of the stages are on, therfore the sound should be terminated
                            osc = osc * 0
                            note.on = False
                            #print('note off')

                            # the envelope is done, but the note is off
                            # ad stage
                            # sound is off
                            # turns the audio off
                            note[5] = False
                            osc = osc * 0
                        elif note[1] > time.time_ns():
                            # the trigger is on
                            # the envelope is good as usual.
                            # TODO: add:
                            # the problem with this implementation is that sustain doesn't work.
                            # neither does relesase because the notes get retriggered instantly.
                            # well time to take a brake for today.
                            # for to accomplish that i think i need a note list/dict, where all of the notes
                            # are stored, even after they have been triggered.
                            osc = osc * lenvs[note[4]]

                            # note[4] doesn't get reset, but the renv needs to start at 0
                            last_note_step = note[4]

                        else:
                            # rel env time
                            print('rastage')
                            osc = osc * renvs[note[4] - last_note_step]
                        '''

            '''
                        osc = osc.astype(np.int16)
                        #plt.plot(osc)
                        #plt.show()
                        #print(note[4])
                        chunks.append(osc)
                        #print('play')

                        #plt.plot(osc)
                        #plt.show()

                        note.chunk_step += 1 # the chunk param

            else:
                # the note must have finished then
                notes.remove(note)


            #chunks.append(wav_chunks[step])

            '''

        #print(chunks)
        play(*chunks)

        #if sample_step >= len(chunks) - 1:
        #    sample_step = 0
        #else: 
        #    sample_step += 1
        #step += 1

    print('all time elapsed ' + str(timer - time.time_ns()))
    
    '''
    for i in range(8):
        new_note(freq=random.randint(-12, 12))

        while len(notes) > 0:
            play_notes()
    '''

    #for chunk in chunks:
    #    stream.write(chunk.astype(np.int16).tobytes())

    #plt.plot(chunks)
    #plt.show()
        #stream.write(chunk.tobytes())
    #print(len(chunks[0]))
    #stream.write(chunks[3].tobytes())


    # write last
    #stream.write(converted_wave.tobytes())

    stream.close()

    p.terminate()
