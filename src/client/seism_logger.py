import os
import sys
import threading

import Adafruit_MCP3008
import websocket

from adc_config import AdcConfig
from data_box import DataBox
from data_filter import DataFilter
from data_processor import DataProcessor
from data_sampler import DataSampler
from data_uploader import DataUploader
from mcp3208 import MCP3208
from rolling_average import RollingAverage
from src.shared.Constants import SEISMOMETER_IDS


class SeismometerConfig(object):
    def __init__(self, seismometer_id):
        self.sampling_rate = 750
        self.decimated_sampling_rate = 30
        self.scale_factor = 8
        self.upload_interval = 4
        self.rolling_average_size = 5 * 60 / self.upload_interval  # 5 minutes rolling average
        self.filter_values = True
        self.filter_cutoff_freq = 6
        self.use_rolling_avg = False
        self.chunk_size = self.sampling_rate * self.upload_interval
        self.adc_config = AdcConfig(seismometer_id)


class AdcWrapper(object):
    def __init__(self, config):
        self.config = config
        if config.adc_bit_resolution == 12:
            self.adc = MCP3208(
                clk=config.CLK, cs=config.CS, miso=config.MISO, mosi=config.MOSI)
        elif config.adc_bit_resolution == 10:
            self.adc = Adafruit_MCP3008.MCP3008(
                clk=config.CLK, cs=config.CS, miso=config.MISO, mosi=config.MOSI)
        else:
            print("Unsupported resulution provided to AdcWrapper")

    def supports_bias_point_measurement(self):
        return self.config.bias_point_channel is not None

    def read_adc(self, channel):
        value = self.adc.read_adc(channel)
        if value == 0 or value == 2 ** self.config.adc_bit_resolution - 1:
            print("Read invalid value:", value)
            return -1
        else:
            return value

    def read_coil(self):
        return self.read_adc(self.config.coil_input_channel)

    def read_bias_point(self):
        return self.read_adc(self.config.bias_point_channel)


class SeismLogger(object):
    def __init__(self, config, ws):
        condition = threading.Condition()
        data_box = DataBox(config.chunk_size)
        rolling_avg = RollingAverage(config.rolling_average_size)
        theoretical_max_value = 2 ** config.adc_config.adc_bit_resolution * config.scale_factor
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

    def start(self):
        sampler_thread = threading.Thread(target=self.data_sampler.run)
        uploader_thread = threading.Thread(target=self.data_uploader.run)
        sampler_thread.daemon = True
        uploader_thread.daemon = True
        uploader_thread.start()
        sampler_thread.start()


def create_web_api_socket(seismometer_id, on_open):
    def on_message(ws, message):
        print(message)

    def on_error(ws, error):
        print(error)

    def on_close(ws, close_status_code, close_msg):
        print("### closed ###")

    web_socket_url = "ws://" + \
                     os.environ.get('API_ENDPOINT') + "/ws/data-logger?seismometer_id=" + seismometer_id
    auth_token = os.environ.get('AUTH_TOKEN')
    ws = websocket.WebSocketApp(web_socket_url,
                                header=["Authorization:" + auth_token],
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    return ws


def start_seism_logger(seismometer_id):
    config = SeismometerConfig(seismometer_id)
    print("starting", '\'' + seismometer_id + '\'')

    def on_websocket_open(ws):
        print("websocket open")
        seism_logger = SeismLogger(config, ws)
        seism_logger.start()

    ws = create_web_api_socket(seismometer_id, on_websocket_open)
    ws.run_forever()


if __name__ == "__main__":
    # websocket.enableTrace(True)
    if 'API_ENDPOINT' not in os.environ:
        print("No API_ENDPOINT defined as env var")
    if 'AUTH_TOKEN' not in os.environ:
        print("No AUTH_TOKEN defined as env var")
    else:
        seismometer_id = sys.argv[1]
        if seismometer_id in SEISMOMETER_IDS:
            start_seism_logger(seismometer_id)
        else:
            print("Invalid seismometer_id:", seismometer_id)
