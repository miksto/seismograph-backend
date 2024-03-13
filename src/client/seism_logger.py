import threading

from websocket import WebSocketApp

from src.client.adc_config import AdcConfig
from src.client.adc_wrapper import AdcWrapper
from src.client.data_box import DataBox
from src.client.data_filter import DataFilter
from src.client.data_processor import DataProcessor
from src.client.data_sampler import DataSampler
from src.client.data_uploader import DataUploader
from src.client.rolling_average import RollingAverage


class SeismometerConfig(object):
    sampling_rate: int
    decimated_sampling_rate: int
    scale_factor: int
    upload_interval: int
    rolling_average_size: int
    filter_values: bool
    filter_cutoff_freq: int
    use_rolling_avg: bool
    chunk_size: int
    adc_config: AdcConfig

    def __init__(self, seismometer_id: str):
        self.sampling_rate = 750
        self.decimated_sampling_rate = 30
        self.scale_factor = 8
        self.upload_interval = 4
        self.rolling_average_size = 5 * 60 // self.upload_interval  # 5 minutes rolling average
        self.filter_values = True
        self.filter_cutoff_freq = 6
        self.use_rolling_avg = False
        self.chunk_size = self.sampling_rate * self.upload_interval
        self.adc_config = AdcConfig(seismometer_id)


class SeismLogger(object):
    def __init__(self, config: SeismometerConfig, ws: WebSocketApp):
        condition = threading.Condition()
        data_box = DataBox(config.chunk_size)
        rolling_avg = RollingAverage(config.rolling_average_size)
        theoretical_max_value: int = 2 ** config.adc_config.adc_bit_resolution * config.scale_factor
        adc = AdcWrapper(config.adc_config)

        if config.filter_values:
            data_filter = DataFilter(config.filter_cutoff_freq, config.sampling_rate)
        else:
            data_filter = None

        data_processor = DataProcessor(config.sampling_rate,
                                       config.decimated_sampling_rate,
                                       rolling_avg,
                                       config.use_rolling_avg,
                                       data_filter)

        self.data_sampler = DataSampler(adc,
                                        condition,
                                        data_box,
                                        config.scale_factor,
                                        config.sampling_rate,
                                        config.upload_interval)

        self.data_uploader = DataUploader(ws,
                                          condition,
                                          data_box,
                                          data_processor,
                                          rolling_avg,
                                          theoretical_max_value,
                                          config.sampling_rate,
                                          config.decimated_sampling_rate)

    def start(self) -> None:
        sampler_thread = threading.Thread(target=self.data_sampler.run)
        uploader_thread = threading.Thread(target=self.data_uploader.run)
        sampler_thread.daemon = True
        uploader_thread.daemon = True
        uploader_thread.start()
        sampler_thread.start()
