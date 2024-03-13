import json
from threading import Condition

import numpy as np
from numpy.typing import NDArray
from websocket import WebSocketApp

from src.client.data_box import DataBox
from src.client.data_processor import DataProcessor
from src.client.rolling_average import RollingAverage


class DataUploader(object):
    ws: WebSocketApp
    condition: Condition
    data_box: DataBox
    data_processor: DataProcessor
    rolling_avg: RollingAverage
    theoretical_max_value: int
    target_sampling_rate: int
    decimated_sampling_rate: int

    def __init__(self,
                 ws: WebSocketApp,
                 condition: Condition,
                 data_box: DataBox,
                 data_processor: DataProcessor,
                 rolling_avg: RollingAverage,
                 theoretical_max_value: int,
                 target_sampling_rate: int,
                 decimated_sampling_rate: int
                 ):
        self.ws = ws
        self.condition = condition
        self.data_box = data_box
        self.data_processor = data_processor
        self.rolling_avg = rolling_avg
        self.theoretical_max_value = theoretical_max_value
        self.target_sampling_rate = target_sampling_rate
        self.decimated_sampling_rate = decimated_sampling_rate

    def upload_data(self, values: NDArray[int], bias_point: int, actual_sampling_rate: int):
        proccessed_values: NDArray[int] = self.data_processor.process(values)
        int_values: NDArray[int] = np.rint(proccessed_values)

        stats = {
            'bias_point': bias_point,
            'actual_sampling_rate': actual_sampling_rate,
            'target_sampling_rate': self.target_sampling_rate,
            'decimated_sampling_rate': self.decimated_sampling_rate,
            'theoretical_max_value': self.theoretical_max_value,
            'rolling_avg': self.rolling_avg.get_average(),
            'batch_avg': sum(values) / len(values),
            'batch_min': int(min(values)),
            'batch_max': int(max(values))
        }
        data_obj = {
            'type': 'post_data',
            'values': int_values.tolist(),
            'stats': stats
        }
        data = json.dumps(data_obj)
        self.ws.send(data)

    def run(self):
        while True:
            with self.condition:
                if not self.data_box.is_full():
                    self.condition.wait()

                values: NDArray[int] = self.data_box.get_values()
                bias_point = self.data_box.bias_point
                actual_sampling_rate = self.data_box.actual_sampling_rate

                self.data_box.clear()
                self.condition.notify()

            self.upload_data(values, bias_point, actual_sampling_rate)
