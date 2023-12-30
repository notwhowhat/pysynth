import modulators
import fx
import note

import numpy as np

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
            if self.note.done:
                self.note = None
            return chunk
        return np.zeros((CHUNK))



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
                #print('on ' + str(self))
                self.note.triggered = True
        else:
            #print('off ' + str(self))
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
            #chunk = 1000 * square(2.0 * np.pi / (44100 / self.note.freq) * indexed_chunk)

            # this makes a simple sloped env for every chunk.
            # next thing to do is to take a long array 
            # for to split it up in chunks now.

            # the envelope needs to be structured in a list
            # containing the envelope specific to the chunks

            # the release gets cut off beacuse of a flawed polyphony/note system
            # every note needs to be an object of a class instead of a list that's nested
            #self.filter.get_afiltered(chunk)
            self.amp.amplify(chunk)

            #plt.plot(chunk)
            #plt.show()
            
            self.note.chunk_step += 1
            if self.note.done:
                self.note = None
            return chunk
        #self.note.chunk_step += 1
        print('zeroead')
        # so basically, the note isn't "on"
        # check why that is.
        return np.zeros((CHUNK))


