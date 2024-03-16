import queue
import threading

from websocket import WebSocketApp

from src.client.adc_wrapper import AdcWrapper
from src.client.data_box import DataBox
from src.client.data_filter import DataFilter
from src.client.data_processor import DataProcessor
from src.client.data_sampler import DataSampler
from src.client.data_uploader import DataUploader
from src.client.rolling_average import RollingAverage
from src.client.seismometer_config import SeismometerConfig


class SeismLogger(object):
    def __init__(self, config: SeismometerConfig, ws: WebSocketApp):
        data_queue = queue.Queue()
        data_box = DataBox(config.chunk_size)
        rolling_avg = RollingAverage(config.rolling_average_size)
        theoretical_max_value: int = 2 ** config.adc_config.adc_bit_resolution * config.scale_factor
        adc = AdcWrapper(config.adc_config)

        if config.filter_config.filter_enabled:
            data_filter = DataFilter(config.filter_config)
        else:
            data_filter = None

        data_processor = DataProcessor(config.sampling_rate,
                                       config.decimated_sampling_rate,
                                       rolling_avg,
                                       config.use_rolling_avg,
                                       data_filter)

        self.data_sampler = DataSampler(adc,
                                        data_queue,
                                        data_box,
                                        config.scale_factor,
                                        config.sampling_rate)

        self.data_uploader = DataUploader(ws,
                                          data_queue,
                                          data_processor,
                                          rolling_avg,
                                          theoretical_max_value,
                                          config.sampling_rate,
                                          config.decimated_sampling_rate)

    def start(self) -> None:
        sampler_thread = threading.Thread(target=self.data_sampler.run, daemon=True)
        uploader_thread = threading.Thread(target=self.data_uploader.run, daemon=True)
        uploader_thread.start()
        sampler_thread.start()
