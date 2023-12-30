import random
CHUNK: int = 1024

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
        self.done: bool = False

        # which chunk it is on.
        self.chunk_step: int = 0
        self.sample_step: int = 0
        self.freq = random.randint(440, 440)


