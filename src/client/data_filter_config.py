from dataclasses import dataclass


@dataclass
class DataFilterConfig(object):
    filter_enabled: bool
    data_sampling_freq: int
    filter_cutoff_freq: int
    filter_order: int
