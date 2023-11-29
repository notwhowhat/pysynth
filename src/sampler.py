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
print(len(envelope))
print('i')
for c in envelope_chunks:
    print(len(c))

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
        if note[5]:
         
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
    for i in range(16):
        # add notes
        #start = current_time + (i * 1000000000 * 2)
        #new_note(start, start + 1000000000 * 2, 's')

        # uncomment under
        start = current_time + (i * whole_note_duration)
        #new_note(start, start + whole_note_duration, 's')
        new_note(start, start + whole_note_duration, 'o')

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
    lenv = np.linspace(0, 2, 25 * CHUNK)
    aenv = np.linspace(0, 16, 10 * CHUNK)
    renv = np.linspace(16, 0, 10 * CHUNK)
    arenv = np.append(aenv, renv)
    for i in range(20):
        #lenvs.append(lenv[i * CHUNK : i * CHUNK + CHUNK]) 
        lenvs.append(arenv[i * CHUNK : i * CHUNK + CHUNK]) 
    # to 
    # to here

    flenv = np.array(())
    for e in lenvs:
        flenv = np.append(flenv, e)
    plt.plot(flenv)
    plt.show()

    print(len(notes))
    print(notes)


    #while True:
    empty_chunk = np.zeros(CHUNK)

    while notes:
        chunks = []
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
            if note[1] > time.time_ns():#current_time:
                if note[0] < time.time_ns():
                    if note[3] == 's': # noise source is sample so step the chunk param
                        # using this implementation the list storing all note data wont be readonly
                        # but python still probably opens it for a write still. well it is probably
                        # quicker to use some more ram than semi-complex math on at least 10^12 numbers

                        # the samples are now pitched
                        if note[4] < len(wav_chunks): # what chunk
                            factor = get_factor(466.164, note[2]) # see the sun is in b flat
                            # speeds induvidual chunks. might not be grate, but it works for now
                            chunks.append(speedx(
                                wav_chunks[note[4]],
                                factor
                            ))

                            note[4] += 1 # the chunk param
                            print(note)

                    if note[3] == 'o': # noise source is osc
                        #osc = 1 * np.sin(2.0 * np.pi / (44100 / 440) * empty_chunk)

                        start = note[4] * CHUNK

                        #indexed_chunk = np.arange(note[4] + 0, note[4] + CHUNK)
                        indexed_chunk = np.arange(start + 0, start + CHUNK)
                        # osc -> oscillation
                        osc = 1000 * np.sin(2.0 * np.pi / (44100 / 440) * indexed_chunk)

                        #osc *= chunk_env
                        #osc *= fade_chunks[note[4]]

                        # vol env time!
                        #print('before ' + str(osc)) 
                        #plt.plot(osc)

                        #osc = envelope_chunks[note[4]] * osc
                        #print('after ' + str(osc)) 


                        # this makes a simple sloped env for every chunk.
                        #osc = osc * qenv

                        # next thing to do is to take a long array 
                        # for to split it up in chunks now.

                        # the envelope needs to be structured in a list
                        # containing the envelope specific to the chunks
                        print(note[4])
                        #osc = osc * lenv
                        # uses lenvs instead of the correct env
                        if note[4] > len(lenvs) - 1:
                            # the envelope is done, but the note is off
                            # sound is off
                            #note[5] = False
                            osc = osc * 0
                        else:
                            # the envelope is good as usual.
                            # TODO: add:
                            # the problem with this implementation is that sustain doesn't work.
                            # neither does relesase because the notes get retriggered instantly.
                            # well time to take a brake for today.
                            # for to accomplish that i think i need a note list/dict, where all of the notes
                            # are stored, even after they have been triggered.
                            osc = osc * lenvs[note[4]]

                        osc = osc.astype(np.int16)
                        #plt.plot(osc)
                        #plt.show()
                        #print(note[4])
                        chunks.append(osc)
                        #print('play')

                        #plt.plot(osc)
                        #plt.show()

                        note[4] += 1 # the chunk param

            else:
                # the note must have finished then
                notes.remove(note)


            #chunks.append(wav_chunks[step])


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

