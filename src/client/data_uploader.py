import json
import queue

import numpy as np
from numpy.typing import NDArray
from websocket import WebSocketApp

from src.client.data_processor import DataProcessor
from src.client.data_uploader_data import DataUploaderData
from src.client.rolling_average import RollingAverage


class DataUploader(object):
    ws: WebSocketApp
    data_queue: queue.Queue[DataUploaderData]
    data_processor: DataProcessor
    rolling_avg: RollingAverage
    theoretical_max_value: int
    target_sampling_rate: int
    decimated_sampling_rate: int

    def __init__(self,
                 ws: WebSocketApp,
                 data_queue: queue.Queue[DataUploaderData],
                 data_processor: DataProcessor,
                 rolling_avg: RollingAverage,
                 theoretical_max_value: int,
                 target_sampling_rate: int,
                 decimated_sampling_rate: int
                 ):
        self.ws = ws
        self.data_queue = data_queue
        self.data_processor = data_processor
        self.rolling_avg = rolling_avg
        self.theoretical_max_value = theoretical_max_value
        self.target_sampling_rate = target_sampling_rate
        self.decimated_sampling_rate = decimated_sampling_rate

    def _upload_data(self, data: DataUploaderData):
        proccessed_values: NDArray[int] = self.data_processor.process(np.array(data.values))
        int_values: NDArray[int] = np.rint(proccessed_values)

        stats = {
            'bias_point': data.bias_point,
            'actual_sampling_rate': data.actual_sampling_rate,
            'target_sampling_rate': self.target_sampling_rate,
            'decimated_sampling_rate': self.decimated_sampling_rate,
            'theoretical_max_value': self.theoretical_max_value,
            'rolling_avg': self.rolling_avg.get_average(),
            'batch_avg': sum(data.values) / len(data.values),
            'batch_min': int(min(data.values)),
            'batch_max': int(max(data.values))
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
            data = self.data_queue.get()
            self._upload_data(data)
            self.data_queue.task_done()
