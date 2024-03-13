import numpy as np


class DataBox(object):
    def __init__(self, max_size):
        self.max_size = max_size
        self.data = []
        self.bias_point = None
        self.actual_sampling_rate = None

    def add(self, data_point):
        self.data.append(data_point)

    def is_full(self):
        return len(self.data) >= self.max_size

    def get_values(self):
        return np.array(self.data)

    def clear(self):
        self.data = []
        self.bias_point = None
        self.actual_sampling_rate = None
