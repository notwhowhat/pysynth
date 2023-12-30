import wave
import sys

import pyaudio

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import square
from scipy.signal import butter 

import time
import random

from voice import Voice
from note import Note

#import keyboard

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
def play(*chunks):
    master_chunk = np.zeros((CHUNK))
    #print(len(chunks))
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

empty_chunk = np.zeros(CHUNK)
voice_count: int = 1

voices = []
for i in range(voice_count):
    voices.append(Voice())

for i in range(3):
    # add notes
    #for j in range(2):
    start = current_time + (10 * i * whole_note_duration)
    notes.append(Note(start, start + 10 * whole_note_duration, 'o'))


#    voices[i].note = notes[0]

# there is something with the trigger, that does so that the voices can't play multiple notes
# simultaniously aswell as only being able to play notes before they have been zero, which
# leads to no audio output.

# investigate further on the trigger.
#voices[0].note = notes[0]
#voices[1].note = notes[1]
#voices[2].note = notes[2]

# this is weird and crazy. i don't think that it is caused by the trigger, because it still exists
# when the amp is disabled, which does so that it has nothing to do with the trigger.


# TODO: just a sligt problem. the notes are always on from the beginning. should
# be simple to fix and related to the note.started variable which is recently added.

def voice_sort(v: Voice) -> int:
    if v.note == None:
        return 0
    else:
        return v.note.start

cycle_counter: int = 0
while notes:
    current_time = time.time_ns()
    chunks = []
    #for voice in voices:
    #    chunks.append(voice.get_chunk())
    #chunks.append(voices[0].get_chunk())
    #voices[0].note.chunk_step += 1 # the chunk param
    started_notes = []

    for note in notes:
        if current_time > note.start:
            # send to voice.
            started_notes.append(note)

    #for note in started_notes:
        #notes.remove(note)
    s_voices = sorted(voices, key=voice_sort)

    for voice in voices:
        if len(started_notes) > 0:
            # it is not empty!

            # now it only works with free voices
            if voice.note == None:
                voice.note = started_notes[0]
                started_notes.pop(0)
                notes.remove(voice.note)
            else:
                # a wacky voice stealing procedure. be carefull at touch!
                if len(s_voices) > 0:
                    s_voices[0].note = started_notes[0]
                    started_notes.pop(0)
                    notes.remove(s_voices[0].note)
                    s_voices.pop(0)

    for v in voices:
        if v.note != None:
            #chunks.append(v.get_chunk(current_time))
            chunks.append(v.get_signal(current_time))
    # sometimes a cycle only takes 0 ns, which is impossible.
    # my guess is that it doesn't get run. checked it, it's the only possible
    # way of it being 0 ns.
    # basically, it doesn't get played, and the chunks don't get generated.

    #print(chunks)
    play(*chunks)

    #print('all time elapsed ' + str(timer - time.time_ns()))
    cycle_counter += 1

stream.close()

p.terminate()

