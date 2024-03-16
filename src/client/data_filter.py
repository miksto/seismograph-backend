from typing import Optional

from numpy.typing import NDArray
from scipy import signal

from src.client.data_filter_config import DataFilterConfig


class DataFilter(object):
    filter_config: DataFilterConfig
    a: NDArray[int]
    b: NDArray[int]
    zi: Optional[NDArray[int]]

    def __init__(self, filter_config: DataFilterConfig):
        self.b, self.a = signal.butter(filter_config.filter_order,
                                       filter_config.filter_cutoff_freq,
                                       fs=filter_config.data_sampling_freq,
                                       btype='low',
                                       analog=False)
        self.zi = None

    def process(self, data: NDArray[int]) -> NDArray[int]:
        if self.zi is None:
            self.zi = signal.lfilter_zi(self.b, self.a) * data[0]

        filtered_data, self.zi = signal.lfilter(
            self.b,
            self.a,
            data,
            zi=self.zi)

        return filtered_data
