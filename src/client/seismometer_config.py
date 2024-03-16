from src.client.adc_config import AdcConfig
from src.client.data_filter_config import DataFilterConfig


class SeismometerConfig(object):
    sampling_rate: int
    decimated_sampling_rate: int
    scale_factor: int
    upload_interval: int
    rolling_average_size: int
    filter_config: DataFilterConfig
    use_rolling_avg: bool
    chunk_size: int
    adc_config: AdcConfig

    def __init__(self, seismometer_id: str, mock_adc: bool):
        self.sampling_rate = 750
        self.decimated_sampling_rate = 30
        self.scale_factor = 8
        self.upload_interval = 4
        self.use_rolling_avg = False
        self.rolling_average_size = 5 * 60 // self.upload_interval  # 5 minutes rolling average
        self.filter_config = DataFilterConfig(
            filter_enabled=True,
            data_sampling_freq=self.sampling_rate,
            filter_cutoff_freq=6,
            filter_order=8
        )
        self.chunk_size = self.sampling_rate * self.upload_interval
        self.adc_config = AdcConfig(seismometer_id, mock_adc)
