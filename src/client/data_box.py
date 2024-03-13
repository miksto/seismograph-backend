from typing import Optional, List

import numpy as np
from numpy.typing import NDArray


class DataBox(object):
    max_size: int
    data: List[int]
    bias_point: Optional[int]
    actual_sampling_rate: Optional[int]

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.data = []
        self.bias_point = None
        self.actual_sampling_rate = None

    def add(self, data_point: int) -> None:
        self.data.append(data_point)

    def is_full(self) -> bool:
        return len(self.data) >= self.max_size

    def get_values(self) -> NDArray[int]:
        return np.array(self.data)

    def clear(self):
        self.data = []
        self.bias_point = None
        self.actual_sampling_rate = None
