from numpy.typing import NDArray

from src.client.data_filter import DataFilter
from src.client.rolling_average import RollingAverage


class DataProcessor(object):
    decimation_factor: int
    data_filter: DataFilter
    rolling_avg: RollingAverage
    use_rolling_avg: bool

    def __init__(self, sampling_rate: int,
                 decimated_sampling_rate: int,
                 rolling_avg: RollingAverage,
                 use_rolling_avg: bool,
                 data_filter: DataFilter):
        self.decimation_factor = sampling_rate // decimated_sampling_rate
        self.data_filter = data_filter
        self.rolling_avg = rolling_avg
        self.use_rolling_avg = use_rolling_avg

    def _decimate(self, values: NDArray[int]) -> NDArray[int]:
        return values[::self.decimation_factor]

    def _get_filtered_values(self, values: NDArray[int]) -> NDArray[int]:
        filtered_data = self.data_filter.process(values)
        decimated_data = self._decimate(filtered_data)
        return decimated_data

    def _get_unfiltered_values(self, values: NDArray[int]) -> NDArray[int]:
        decimated_data = self._decimate(values)
        return decimated_data

    def process(self, values: NDArray[int]) -> NDArray[int]:
        self.rolling_avg.add_batch(values)

        if self.use_rolling_avg:
            values = values - self.rolling_avg.get_average()

        if self.data_filter is not None:
            return self._get_filtered_values(values)
        else:
            return self._get_unfiltered_values(values)
