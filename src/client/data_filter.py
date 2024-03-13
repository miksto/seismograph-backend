from scipy import signal


class DataFilter(object):
    def __init__(self, filter_cutoff_freq, sampling_rate):
        self.sampling_rate = sampling_rate
        nyquist_freq = sampling_rate / 2
        wn = filter_cutoff_freq / nyquist_freq
        self.b, self.a = signal.butter(4, wn, btype='lowpass')
        # Simplified way
        # self.b, self.a = signal.butter(4, filter_cutoff_freq, fs=sampling_rate, btype='low', analog=False)
        self.zi = signal.lfilter_zi(self.b, self.a)

    def process(self, data):
        values, self.zi = signal.lfilter(
            self.b,
            self.a,
            data,
            zi=self.zi
        )
        return values
