from numpy.typing import NDArray
from scipy import signal


class DataFilter(object):
    sampling_rate: int
    a: NDArray[int]
    b: NDArray[int]
    zi: NDArray[int]

    def __init__(self, filter_cutoff_freq: int, sampling_rate: int):
        self.sampling_rate = sampling_rate
        self.b, self.a = signal.butter(4,
                                       filter_cutoff_freq,
                                       fs=sampling_rate,
                                       btype='low',
                                       analog=False)
        self.zi = signal.lfilter_zi(self.b, self.a)

    def process(self, data: NDArray[int]) -> NDArray[int]:
        values, self.zi = signal.lfilter(
            self.b,
            self.a,
            data,
            zi=self.zi
        )
        return values
