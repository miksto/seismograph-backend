import json

import numpy as np


class DataUploader(object):
    def __init__(self, ws, condition, data_box, data_processor, rolling_avg, theoretical_max_value,
                 target_sampling_rate,
                 decimated_sampling_rate):
        self.ws = ws
        self.condition = condition
        self.data_box = data_box
        self.data_processor = data_processor
        self.rolling_avg = rolling_avg
        self.theoretical_max_value = theoretical_max_value
        self.target_sampling_rate = target_sampling_rate
        self.decimated_sampling_rate = decimated_sampling_rate

    def upload_data(self, values, bias_point, actual_sampling_rate):
        proccessed_values = self.data_processor.process(values)
        int_values = np.rint(proccessed_values)

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

                values = self.data_box.get_values()
                bias_point = self.data_box.bias_point
                actual_sampling_rate = self.data_box.actual_sampling_rate

                self.data_box.clear()
                self.condition.notify()

            self.upload_data(values, bias_point, actual_sampling_rate)
