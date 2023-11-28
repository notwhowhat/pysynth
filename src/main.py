# just a small prototype/test.

import pyaudio
import numpy as np
from scipy.signal import sawtooth as scitooth
from scipy.signal import square
import keyboard
import matplotlib.pyplot as plt
import time
import random
import wave

CHUNK = 1024
SAMPLE_WIDTH = 2
CHANNELS = 1
SAMPLE_RATE = 44100

# open the stream
p = pyaudio.PyAudio()

stream = p.open(
    format=pyaudio.paFloat32,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    output=True,
    frames_per_buffer=CHUNK,
)

# supersaw test wooohoooo!
# not any more...

# adsr envelope time! lets fold this code :)

# now ive kindof got modulating going, so i think the next step is a sequencer... :D

# attack
a_time = int(0.00 * SAMPLE_RATE)
a_level = 2
# decay
d_time = int(0.0 * SAMPLE_RATE)
# sustain
s_time = int(0.001 * SAMPLE_RATE)
s_level = 1
# release
r_time = int(0.0 * SAMPLE_RATE)

# full envelope
attack = np.linspace(0, a_level, a_time)
decay = np.linspace(a_level, s_level, d_time)
sustain = np.full((s_time, ), s_level)
release = np.linspace(s_level, 0, r_time)

# similar envs are added while different ones are separated
ad_env = np.append(attack, decay)
step_ad_env = 0

s_env = sustain
step_s_env = 0

r_env = release
step_r_env = 0

start = 0

envelope_step = 0
note_on = False
sound_on = False
note_start = False

note_trigger = False

# might change the sequencing to velocity-based instead of note-on/off
# now i have a weird system for long notes...

sequence_velocities = [1, 1, 1, 1]
sequence_frequencies = [440, 440, 440, 440]
sequence_note_starts = [True, True, True, True]
step_sequence = 0

frequency = 1
velocity = 0

#if len(sequence_velocities) == len(sequence_frequencies):
#    print('sequencer works...')

clock = 0
start_step = time.time_ns()

# measure fixed to 4/4 now!
# the bpm actually works now...
bpm = 120
note_resolution = 1
bpm_mul = (bpm / 60) * note_resolution
step_time = int(1000000000 / bpm_mul)
print(step_time)

bar_time = int(1000000000 / bpm_mul)
bar_start_time = time.time_ns()
sixteenth_note = int(1000000000 / (bpm_mul * 16))

# time to use som ms instead of classical stuff!
# ehh forget that lets start sampling!
time_sequence_starts =  [0, sixteenth_note, 2 * sixteenth_note, 3 * sixteenth_note]
time_sequence_durations = [(sixteenth_note / 3 * 4), (sixteenth_note / 3 * 4), (sixteenth_note / 3 * 4), (sixteenth_note / 3 * 4)]

# loading a file for sampling!
sample = []
sample_start = 0
step_sample = 0

while True:
    # simple keyboardish functionallity
    # these checks must be done before the data is generated for to be able to 
    # use a volume envelope

    # time sequencing is kindof hard... yeah lets sample instead :D

    # step sequencer! but thats oldschool
    if start_step + step_time < time.time_ns():
     
        step_sequence += 1
        start_step = time.time_ns()

    if step_sequence >= len(sequence_velocities):
        step_sequence = 0

    if sequence_velocities[step_sequence] > 0:
        note_trigger = True
        frequency = sequence_frequencies[step_sequence]
        velocity = sequence_velocities[step_sequence]
        note_start = sequence_note_starts[step_sequence]
    else:
        note_trigger = False
    
    if note_trigger:
        if note_start:
            if start_step == time.time_ns():
                step_ad_env = 0
                step_s_env = 0
                step_r_env = 0
                s_env = sustain 

        note_on = True
        sound_on = True
    else:
        note_on = False

    empty_data = np.arange(start, start + CHUNK)
    data = np.array([])

    # just a simple sine-wave
    #samples = 0.1 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 440) * empty_data)
    samples = velocity * 0.1 * np.sin(2.0 * np.pi / (SAMPLE_RATE / frequency) * empty_data)
    '''
    if step_sample < len(sample) - 1:
        step_sample = 0
    else:
        step_sample += 1
    samples = sample[step_sample]
    #step_sample = 3
    data = samples
    #print(data)
    '''

    for i, sample in enumerate(samples):
        if step_ad_env < len(ad_env):
            sample *= ad_env[step_ad_env]
            step_ad_env += 1
            data = np.append(data, sample)
        elif step_s_env < len(s_env):
            sample *= s_env[step_s_env]
            step_s_env += 1
            data = np.append(data, sample)
            if note_on:
                s_env = np.append(s_env, s_level)
        elif step_r_env < len(r_env):
            sample *= r_env[step_r_env]
            step_r_env += 1
            data = np.append(data, sample)
        else:
            sample *= 0
            data = np.append(data, sample)

            sound_on = False

    start += CHUNK
    if start == CHUNK * SAMPLE_RATE:
        start = 0

    # do last!!!
    stream.write(data.astype(np.float32).tobytes())
    #stream.write(data)
    clock += 1


stream.close()
print('stream closed')

# the plotting is saved for if i might need it
'''
empty_data = np.arange(start, start + CHUNK)

# just a simple sine-wave
samples = 0.1 * square(2.0 * np.pi / (SAMPLE_RATE / 440) * empty_data)
print(samples)
data = np.array([])

for i, sample in enumerate(samples):
    if envelope_step < len(envelope):
        sample *= envelope[envelope_step]
        envelope_step += 1
        data = np.append(data, sample)
#data = samples

plt.plot(samples)
plt.plot(envelope)
plt.plot(data)
plt.show()
'''



