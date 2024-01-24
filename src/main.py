import wave
import sys

import pyaudio

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import square
from scipy.signal import butter 

import time
import random
import keyboard
import colorama

from globals import *
from helpers import get_factor

from voice import Voice
from note import Note

colorama.init()


#CHUNK = 1024

# only try files in mono, at 44100hz
file = '../see_the_sun.wav'
sampler_sample = []
sample_step = 0
note_on = True
play_list = []

bass_freq = 466.16

#sample_duration_ns = 44100 / 1000000000
# at 44.1Khz one sample is 0.00002267573 seconds
sample_duration_ns = 1000000000 / 44100

bpm = 120
whole_note_duration = int(60000000000 / 120)
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
        rate=SAMPLE_RATE,
        output=True
)

current_time = time.time_ns()

empty_chunk = np.zeros(CHUNK)
voice_count: int = 32

voices = []
for i in range(voice_count):
    voices.append(Voice())

all_notes: list = []
notes: list = []
keyboard_notes: list = []

class Key:
    def __init__(self, key: 'str', freq: float) -> None:
        self.key = key
        self.freq = freq
        self.on = False

keyboard_histr  = "   W | E       T | Y | U       O | P "
keyboard_midstr = " ----------------------------------- "
keyboard_lowstr = " A | S | D | F | G | H | J | K | L   "

keyboard_keys: list = [
    'a', 'w', 's', 'e',
    'd', 'f', 't', 'g',
    'y', 'h', 'u', 'j',
]

# a, which is located at this index has 440 hz.
a_index: int = 11 - 9

# XXX: be ware of crazy code.
keys: list = []
for i, k in enumerate(reversed(keyboard_keys)):
    freq_factor: float = get_factor(440, i - a_index)
    freq: float = 440 * freq_factor

    keys.append(Key(key=k, freq=freq))
    print('f:', freq, 'k:', k)


def play(*chunks):
    master_chunk = np.zeros((CHUNK))
    #print(len(chunks))
    for chunk in chunks:
        #if len(chunk) == CHUNK:
        master_chunk += chunk

    #master_chunk /= len(chunks)

    #plt.plot(master_chunk)
    #plt.show()

    print('notes len', len(notes), 'chunks', len(chunks))
    stream.write(master_chunk.astype(np.int16).tobytes())

for i, e in enumerate(keys):
    start = (2 * i * whole_note_duration)
    notes.append(Note(e, start=start, end=start + 1 * whole_note_duration, sequencer=True))

def voice_sort(v: Voice) -> int:
    if v.note == None or v.note.start == None:
        return 0
    else:
        return v.note.start

cycle_counter: int = 0
start_time: int = time.time_ns()

voice_stealing: bool = False

# what i need to do now:
# make a loop/pattern mode
# for that i need a sequencer/looper kindof thing, that can send notes to the manager.
# do this by making the relative time do stuff.


# all notes that are on, or that have been or that will be should end up here.
# TODO: fix this and make it better.
# time for a major arcetectural upgrade.
# instead of directly checking the note times for to see if they are on, it will instead
# just check how the states are.
# the states will then be set by either a sequencer or manual input through a keyboard.

output: np.ndarray = np.array(())

# the stuttering isn't compleetly fixed. it comes after plating ten notes on the sequencer.
plot: bool = False

print('Initialization finished')
try:
    while True:
        #print('\x1b[1A\x1b[2K')
        current_time = time.time_ns()
        relative_time = current_time - start_time
        chunks = []

        for key in keys:
            # insane ammounts of lag...
            if keyboard.is_pressed(key.key):
                if key.on == False:
                    #note: Note = Note(start=relative_time, end=relative_time + 10 * whole_note_duration, freq=key.freq)
                    note: Note = Note(key)
                    all_notes.append(note)
                    notes.append(note)
                    keyboard_notes.append(note)

                    print('note added')
                    key.on = True
            else:
                key.on = False

        # all of the voice handeling code
        started_notes = []

        for note in notes:
            if note.start != None:
                if relative_time > note.start:
                    # send to voice.
                    started_notes.append(note)
            else:
                started_notes.append(note)

        #for note in started_notes:
            #notes.remove(note)
        s_voices = sorted(voices, key=voice_sort)

        for voice in voices:
            if len(started_notes) > 0:
                # it is not empty!

                # now it only works with free voices
                # XXX: basically this is why the envelope gets reset. instead of checking the free voices first,
                # so the free voices need to be added to s_voices.
                if voice.note == None:
                    voice.note = started_notes[0]
                    started_notes.pop(0)
                    notes.remove(voice.note)
                else:
                    
                    if voice_stealing:
                        # a wacky voice stealing procedure. be carefull at touch!
                        if len(s_voices) > 0:
                            s_voices[0].note = started_notes[0]
                            started_notes.pop(0)
                            notes.remove(s_voices[0].note)
                            s_voices.pop(0)

        chunks = [np.zeros((CHUNK))]
        notecnt = 0
        for i, v in enumerate(voices):
            if v.note != None:
                #chunks.append(v.get_chunk(current_time))
                chunk: np.ndarray = np.zeros((CHUNK))

                for i, e in enumerate(chunk):
                    #chunk[i] = v.get_signal(relative_time)
                    chunk[i] = v.get_sample(0, relative_time)

                # this singlehandedly fixed the stuttering isue.
                if chunk[-1] == 0:
                    v.note = None

                #c = v.get_signal(relative_time)
                #chunks.append(v.get_signal(relative_time))
                chunks.append(chunk)
                #output = np.append(output, c)
            else:
                notecnt += 1
        # sometimes a cycle only takes 0 ns, which is impossible.
        # my guess is that it doesn't get run. checked it, it's the only possible
        # way of it being 0 ns.
        # basically, it doesn't get played, and the chunks don't get generated.

        #print(chunks)
        play(*chunks)

        #print('all time elapsed ' + str(timer - time.time_ns()))
        cycle_counter += 1
        #osc_step += 1
        osc_step += 1
except:
    pass
stream.close()
p.terminate()


