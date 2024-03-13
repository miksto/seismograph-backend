import time


class DataSampler(object):
    def __init__(self, adc, condition, data_box, scale_factor, sampling_rate, upload_interval):
        self.condition = condition
        self.target_sampling_rate = sampling_rate
        self.sleep_time = 1 / (sampling_rate / 0.5)
        self.adc = adc
        self.data_box = data_box
        self.scale_factor = scale_factor

    def fill_data_box(self):
        if self.adc.supports_bias_point_measurement():
            self.data_box.bias_point = self.adc.read_bias_point() * self.scale_factor

        while not self.data_box.is_full():
            value = self.adc.read_coil() * self.scale_factor
            if value > 0:
                self.data_box.add(value)

            if not self.data_box.is_full():
                time.sleep(self.sleep_time)

    def _adjust_sleep_time(self, time_diff):
        actual_sampling_rate = self.data_box.max_size / (time_diff)
        sampling_rate_error_fraction = actual_sampling_rate / self.target_sampling_rate
        self.sleep_time = (self.sleep_time + (self.sleep_time * sampling_rate_error_fraction)) / 2
        self.data_box.actual_sampling_rate = actual_sampling_rate

    def run(self):
        while True:
            with self.condition:
                if self.data_box.is_full():
                    self.condition.wait()

                t1 = time.time()
                self.fill_data_box()
                t2 = time.time()
                self._adjust_sleep_time(t2 - t1)
                self.condition.notify()
