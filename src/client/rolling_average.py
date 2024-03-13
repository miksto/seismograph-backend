from typing import List

from numpy.typing import NDArray


class RollingAverage(object):
    _avg_list: List = []
    max_size: int

    def __init__(self, max_size: int):
        self.max_size = max_size

    def _trim_size(self) -> None:
        if len(self._avg_list) > self.max_size:
            self._avg_list.pop()

    def _add(self, value) -> None:
        self._avg_list.insert(0, value)
        self._trim_size()

    def add_batch(self, values: NDArray[int]) -> None:
        avg = sum(values) / len(values)
        self._add(avg)

    def is_empty(self) -> bool:
        return not self._avg_list

    def get_average(self) -> float:
        current_size = len(self._avg_list)
        if current_size > 0:
            val_sum = 0
            weight_sum = 0
            for id, val in enumerate(self._avg_list, start=2):
                weight = 1 / id
                val_sum += weight * val
                weight_sum += weight

            return val_sum / weight_sum
        else:
            return 0
