class DataProcessor(object):
    def __init__(self, sampling_rate, decimated_sampling_rate, rolling_avg, use_rolling_avg, data_filter):
        self.decimation_factor = sampling_rate // decimated_sampling_rate
        self.data_filter = data_filter
        self.rolling_avg = rolling_avg
        self.use_rolling_avg = use_rolling_avg

    def _decimate(self, values):
        return values[::self.decimation_factor]

    def _get_filtered_values(self, values):
        filtered_data = self.data_filter.process(values)
        decimated_data = self._decimate(filtered_data)
        return decimated_data

    def _get_unfiltered_values(self, values):
        decimated_data = self._decimate(values)
        return decimated_data

    def process(self, values):
        self.rolling_avg.add_batch(values)

        if self.use_rolling_avg:
            values = values - self.rolling_avg.get_average()

        if self.data_filter is not None:
            return self._get_filtered_values(values)
        else:
            return self._get_unfiltered_values(values)
