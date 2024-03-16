from dataclasses import dataclass
from typing import List


@dataclass
class DataUploaderData(object):
    values: List[int]
    bias_point: int
    actual_sampling_rate: int
