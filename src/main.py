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

from globals import *
from helpers import get_factor

from voice import Voice
from note import Note


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
# make the timings relative, because otherwise the load times of the notes
# do so that they don't get played, because the loading is 1.1+ seconds, when a note
# can be less than 1 sec.
# this does so that notes get triggered before they get played, sometimes a few seconds
# and then they don't get played.
# done!!!

# will be done now.

empty_chunk = np.zeros(CHUNK)
voice_count: int = 16
# one of my things don't work so well, so everything starts to stutter if there are more than 2 voices.
# one of the notes doesn't turn off

# bassically, it works when the chunk getting inputted are 2, otherwise, it starts to stutter.
# after the first 2 notes, it becomes 3.
# what is the difference with the second and third notes? well one of the second voice has the note for the first time. not the third.
# that's not really how it works. it is more that it happens at note 7 or 8.

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

    #plt.plot(master_chunk)
    #plt.show()

    print('notes len', len(notes), 'chunks', len(chunks))
    stream.write(master_chunk.astype(np.int16).tobytes())


# basically the stutter bug is not based on clipping. instead it is because too 
# many notes are getting passed into the master chunk at once, even those that are turned off.
# this probably got implemented when i changed the states for the note system, but forgot to do
# so that some get removed from being sent to the chunks.

# i have gotten closer to solving the bug. something is weird, because after the first and second notes
# being played and finished, only one less note is none, which is the normal behaviour actually. instead,
# the notes after are played, but not put to none. weird!



#for i in range(3):
for i, e in enumerate(keys):
    # add notes

    # time for relative times!
    #start = current_time + (10 * i * whole_note_duration)
    start = (4 * i * whole_note_duration)
    #notes.append(Note(start=start, end=start + 10 * whole_note_duration))

    # key needs to be passed.
    # done!
    #notes.append(Note(start=start, end=start + 10 * whole_note_duration))
    #notes.append(Note(keys[0], start=start, end=start + 10 * whole_note_duration, sequencer=True))
    notes.append(Note(e, start=start, end=start + 2 * whole_note_duration, sequencer=True))
    #notes.append(Note(e, start=start, end=start + 5 * whole_note_duration, sequencer=True))



# there is something with the trigger, that does so that the voices can't play multiple notes
# simultaniously aswell as only being able to play notes before they have been zero, which
# leads to no audio output.

def voice_sort(v: Voice) -> int:
    if v.note == None or v.note.start == None:
        return 0
    else:
        return v.note.start

cycle_counter: int = 0
start_time: int = time.time_ns()

voice_stealing: bool = True

space_note: bool = False

# all notes that are on, or that have been or that will be should end up here.
# TODO: fix this and make it better.
# time for a major arcetectural upgrade.
# instead of directly checking the note times for to see if they are on, it will instead
# just check how the states are.
# the states will then be set by either a sequencer or manual input through a keyboard.

output: np.ndarray = np.array(())
outputs: list = [
    np.array(()),
    np.array(()),
    np.array(()),
    np.array(()),
]

print('Initialization finished')
try:
    while True:
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

                #c = v.get_signal(relative_time)
                #chunks.append(v.get_signal(relative_time))
                chunks.append(chunk)
                #output = np.append(output, c)
                pass
            else:
                notecnt += 1
        print(notecnt)
        # sometimes a cycle only takes 0 ns, which is impossible.
        # my guess is that it doesn't get run. checked it, it's the only possible
        # way of it being 0 ns.
        # basically, it doesn't get played, and the chunks don't get generated.

        #print(chunks)
        play(*chunks)

        #print('all time elapsed ' + str(timer - time.time_ns()))
        cycle_counter += 1
except KeyboardInterrupt:
    plt.plot(output)
    plt.show()

stream.close()

p.terminate()

