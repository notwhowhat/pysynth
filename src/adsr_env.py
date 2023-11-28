# just a small prototype/test.

import pyaudio
import numpy as np
from scipy.signal import sawtooth as scitooth
from scipy.signal import square
import keyboard
import matplotlib.pyplot as plt

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

'''
# attack
a_time = int(0.5 * SAMPLE_RATE)
a_level = 2
# decay
d_time = int(0.6 * SAMPLE_RATE)
# sustain
s_time = int(0.1 * SAMPLE_RATE)
s_level = 1
# release
r_time = int(0.8 * SAMPLE_RATE)

# full envelope
attack = np.linspace(0, a_level, a_time)
decay = np.linspace(a_level, s_level, d_time)
sustain = np.full((s_time, ), s_level)
release = np.linspace(s_level, 0, r_time)

#envelope = np.append(attack, decay, sustain, release)
envelope = np.append(attack, decay)
envelope = np.append(envelope, sustain)
envelope = np.append(envelope, release)
'''

# attack
a_time = int(0.5 * SAMPLE_RATE)
a_level = 2
# decay
d_time = int(0.2 * SAMPLE_RATE)
# sustain
s_time = int(0.001 * SAMPLE_RATE)
s_level = 1
# release
r_time = int(0.5 * SAMPLE_RATE)

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

# HACK
old_s_time = s_time


while True:
        # simple keyboardish functionallity
    # these checks must be done before the data is generated for to be able to 
    # use a volume envelope
    if keyboard.is_pressed('space'):
        if note_on == False:
            note_start = True
            step_ad_env = 0
            step_s_env = 0
            step_r_env = 0

            s_env = sustain
     
        else:
            note_start = False
        note_on = True
        sound_on = True
    else:
        note_on = False
    #if note_on:
        #s_time += 1
        #sustain = np.full((s_time,), s_level)
 

    # the note is off during this iteration
    #if note_on == False:
    #    note_start = True
    #else:
    #    note_start = False

    if note_start:
        # start the envelope generator!

        # the envelope starting step is reset
        #step_ad_env = 0
        #step_s_env = 0
        #step_r_env = 0
        '''
        '''
        
        


    empty_data = np.arange(start, start + CHUNK)
    data = np.array([])

    # just a simple sine-wave
    samples = 0.1 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 440) * empty_data)

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


    # non-functional optimised way...
    # who needs optimisations?? :)
    '''
    for i, sample in enumerate(samples):
        if envelope_step < a_time:#len(envelope):
            sample *= attack[envelope_step]
            envelope_step += 1
            data = np.append(data, sample)

        elif envelope_step < a_time + d_time:#len(envelope):
            sample *= decay[envelope_step - a_time]
            envelope_step += 1
            data = np.append(data, sample)

        elif envelope_step < a_time + d_time + s_time:#len(envelope):
            sample *= sustain[envelope_step - a_time - d_time]
            envelope_step += 1
            data = np.append(data, sample)
            s_time += 1

        #elif envelope_step < a_time + d_time + s_time + r_time:#len(envelope):
        elif envelope_step > s_time:#len(envelope):
            sample *= release[envelope_step - a_time - d_time - s_time]
            envelope_step += 1
            print(envelope_step)
            data = np.append(data, sample)



        else:
            note_on = False
            i * 0
            print('bye')
    '''


    '''
    for i, sample in enumerate(samples):
        if envelope_step < len(envelope):
            sample *= envelope[envelope_step]
            envelope_step += 1
            data = np.append(data, sample)
        else:
            note_on = False
            i * 0
            print('bye')
    '''




    start += CHUNK
    if start == CHUNK * SAMPLE_RATE:
        start = 0

    stream.write(data.astype(np.float32).tobytes())


stream.close()
print('stream closed')

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
    else:
        note_on = False
        i * 0
        print('bye')

#data = samples

plt.plot(samples)
plt.plot(envelope)
plt.plot(data)
plt.show()
'''

'''
    s1 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 440) * empty_data)

    s2 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 440.1) * empty_data)
    s3 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 440.2) * empty_data)
    s4 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 440.3) * empty_data)

    s5 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 439.9) * empty_data)
    s6 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 439.8) * empty_data)
    s7 = 0.05 * scitooth(2.0 * np.pi / (SAMPLE_RATE / 439.7) * empty_data)

    side_1 = np.add(s1, s2, s3)
    side_2 = np.add(s4, s5, s6)
    data = np.add(side_1, side_2)
    data = s1

    #data = 0.05 * np.arctan(np.tan(2.0 * np.pi / (SAMPLE_RATE / 440) * empty_data))
    '''





