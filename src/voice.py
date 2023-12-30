import modulators
import fx
import note

import numpy as np
import matplotlib.pyplot as plt

CHUNK: int = 1024

class Voice:
    def __init__(self) -> None:
        # the voice's purpoouse is to be able to use instances for the notes.
        # handles and playes the note that is sent to it.
        self.amp: Amp = fx.Amp(self)
        self.filter: Filter = fx.Filter(self)
        self.note: note.Note = None

        # time for major strutural revamp out of nowwhere!!!
        # instead of passing a whole chunk through the whole signal chain it will instead
        # do everything sample-wise.

        # TODO: the problem comes when i get to the envelopes. they are based on chunks. i can change it,
        # bu then i also need to change the chunk_step in the note, which can break the sampler, because it is
        # based on it.

    def get_signal(self, current_time: int) -> np.ndarray:
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
                #print('on ' + str(self))
                self.note.triggered = True
        else:
            #print('off ' + str(self))
            self.note.triggered = False
        #return np.zeros((CHUNK))

        self.note.on = True

        if self.note.on:
            start = self.note.chunk_step * CHUNK
            empty_chunk = np.arange(start, start + CHUNK)
            chunk = np.array(())

            for e in empty_chunk:
                # signal will be generated sample-wise
                sample: float = np.sin(2.0 * np.pi / (44100 / self.note.freq) * e)
                sample = self.amp.amplify(sample)
                chunk = np.append(chunk, sample)

                # the sample step must be incremented every sample
                self.note.sample_step += 1

            self.note.chunk_step += 1
            # there is some uneaven problem which occurs when note.on always is on, which results in
            # the phases are off sync, which gives a buzzy and unpleasant sound. 

            #if self.note.done:
            #    self.note = None
            #plt.plot(chunk)
            #plt.show()
            return chunk
        return np.zeros((CHUNK))


