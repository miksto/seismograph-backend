import queue
import time

from src.client.adc_wrapper import AdcWrapper
from src.client.data_box import DataBox
from src.client.data_uploader_data import DataUploaderData


class DataSampler(object):
    data_queue: queue.Queue[DataUploaderData]
    target_sampling_rate: int
    actual_sampling_rate: int
    sleep_time: float
    adc: AdcWrapper
    data_box: DataBox
    scale_factor: int

    def __init__(self,
                 adc: AdcWrapper,
                 data_queue: queue.Queue[DataUploaderData],
                 data_box: DataBox,
                 scale_factor: int,
                 sampling_rate: int):
        self.data_queue = data_queue
        self.target_sampling_rate = sampling_rate
        self.sleep_time = 1 / (sampling_rate / 0.5)
        self.adc = adc
        self.data_box = data_box
        self.scale_factor = scale_factor

    def _fill_data_box(self) -> None:
        while not self.data_box.is_full():
            value = self.adc.read_coil() * self.scale_factor
            self.data_box.add(value)
            time.sleep(self.sleep_time)

    def _publish_data_to_queue(self) -> None:
        bias_point = None
        if self.adc.supports_bias_point_measurement():
            bias_point = self.adc.read_bias_point() * self.scale_factor

        self.data_box.prepare_for_data_upload()
        self.data_queue.put(
            DataUploaderData(
                values=self.data_box.data_to_upload,
                bias_point=bias_point,
                actual_sampling_rate=self.actual_sampling_rate
            )
        )

    def _adjust_sleep_time(self, time_diff) -> None:
        self.actual_sampling_rate = self.data_box.max_size / time_diff
        sampling_rate_error_fraction = self.actual_sampling_rate / self.target_sampling_rate
        self.sleep_time = (self.sleep_time + (self.sleep_time * sampling_rate_error_fraction)) / 2

    def run(self) -> None:
        while True:
            t1 = time.time()
            self._fill_data_box()
            t2 = time.time()
            self._adjust_sleep_time(t2 - t1)
            self._publish_data_to_queue()
