import datetime
import json
import os
import random
import sys
import threading
import time

import numpy as np
import websocket
from scipy import signal

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# Software SPI configuration:
CLK = 18
MISO = 23
MOSI = 24
CS = 25

ADC_CHANNEL = 2


class MCP3208(Adafruit_MCP3008.MCP3008):
    # Modification to support the 12 bits ADC
    def read_adc(self, adc_number):
        """Read the current value of the specified ADC channel (0-7).  The values
        can range from 0 to 1023 (10-bits).
        """
        assert 0 <= adc_number <= 7, 'ADC number must be a value of 0-7!'
        # Build a single channel read command.
        # For example channel zero = 0b11000000
        command = 0b11 << 6                  # Start bit, single channel read
        command |= (adc_number & 0x07) << 3  # Channel number (in 3 bits)
        # Note the bottom 3 bits of command are 0, this is to account for the
        # extra clock to do the conversion, and the low null bit returned at
        # the start of the response.
        resp = self._spi.transfer([command, 0x0, 0x0])
        # Parse out the 12 bits of response data and return it.
        result = (resp[0] & 0x01) << 11  # only B11 is here
        result |= resp[1] << 3           # B10:B3
        # MSB has B2:B0 ... need to move down to LSB
        result |= resp[2] >> 5
        return (result & 0x0FFF)  # ensure we are only sending 12b


class DataFilter(object):
    def __init__(self, sampling_rate):
        self.sampling_rate = sampling_rate
        nyquist_freq = sampling_rate / 2
        filter_cutoff_freq = 1.2  # Hz
        wn = filter_cutoff_freq / nyquist_freq
        self.b, self.a = signal.butter(4, wn, btype='lowpass')
        self.zi = signal.lfilter_zi(self.b, self.a)

    def process(self, data):
        values, self.zi = signal.lfilter(
            self.b,
            self.a,
            data,
            zi=self.zi
        )
        return values


class RollingAverage(object):
    _avg_list = []

    def __init__(self, max_size):
        self.max_size = max_size

    def _trim_size(self):
        if len(self._avg_list) > self.max_size:
            self._avg_list.pop()

    def _add(self, value):
        self._avg_list.insert(0, value)
        self._trim_size()

    def add_batch(self, values):
        avg = sum(values) / len(values)
        self._add(avg)

    def is_empty(self):
        return not self._avg_list

    def get_average(self):
        current_size = len(self._avg_list)
        if current_size > 0:
            val_sum = 0
            weight_sum = 0
            for id, val in enumerate(self._avg_list, start=2):
                weight = 1/id
                val_sum += weight* val
                weight_sum += weight

            return val_sum / weight_sum
        else:
            return 0


class DataBox(object):
    def __init__(self, max_size):
        self.max_size = max_size
        self.data = []

    def add(self, data_point):
        self.data.append(data_point)

    def is_full(self):
        return len(self.data) >= self.max_size

    def get_values(self):
        return np.array(self.data)

    def clear(self):
        self.data = []


class DataProcessor(object):
    def __init__(self, sampling_rate, decimated_sampling_rate, rolling_average_size, filter_values):
        self.filter_values = filter_values
        self.decimation_factor = sampling_rate // decimated_sampling_rate
        self.filter = DataFilter(sampling_rate)
        self.rolling_avg = RollingAverage(rolling_average_size)

    def _get_filtered_values(self, values):
        filtered_data = self.filter.process(values)
        decimated_data = signal.decimate(filtered_data, self.decimation_factor)
        return decimated_data

    def _get_unfiltered_values(self, values):
        decimated_data = signal.decimate(values, self.decimation_factor)
        return decimated_data

    def process(self, values):
        self.rolling_avg.add_batch(values)
        values = values - self.rolling_avg.get_average()
        
        if self.filter_values:
            return self._get_filtered_values(values)
        else:
            return self._get_unfiltered_values(values)


class DataSampler(object):
    def __init__(self, condition, data_box, sampling_rate, upload_interval):
        self.condition = condition
        self.sampling_rate = sampling_rate
        self.sleep_time = 1/(sampling_rate/0.5)
        self.mcp = MCP3208(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
        self.data_box = data_box

    def fill_data_box(self):
        while not self.data_box.is_full():
            value = self.mcp.read_adc(ADC_CHANNEL)
            self.data_box.add(value)

            if not self.data_box.is_full():
                time.sleep(self.sleep_time)

    def _adjust_sleep_time(self, time_diff):
        actual_sampling_rate = self.data_box.max_size / (time_diff)
        sampling_rate_error_fraction = actual_sampling_rate / self.sampling_rate
        self.sleep_time = self.sleep_time * sampling_rate_error_fraction

    def run(self):
        while True:
            with self.condition:
                if self.data_box.is_full():
                    self.condition.wait()

                t1 = time.time()
                self.fill_data_box()
                t2 = time.time()
                self.condition.notify()
                self._adjust_sleep_time(t2-t1)


class DataUploader(object):
    def __init__(self, ws, condition, data_box, scale_factor, data_processor):
        self.ws = ws
        self.condition = condition
        self.data_box = data_box
        self.scale_factor = scale_factor
        self.data_processor = data_processor

    def upload_data(self, values):
        int_values = np.rint(values * self.scale_factor)
        data = '{"values": ' + \
            json.dumps(int_values.tolist()) + ', "type": "post_data"}'
        self.ws.send(data)

    def run(self):
        while True:
            with self.condition:
                if not self.data_box.is_full():
                    self.condition.wait()

                values = self.data_box.get_values()
                self.data_box.clear()
                self.condition.notify()

            proccessed_values = self.data_processor.process(values)
            self.upload_data(proccessed_values)


class SeismLogger(object):
    sampling_rate = 750
    decimated_sampling_rate = 15
    scale_factor = 8
    upload_interval = 10
    rolling_average_size = 5 * 60 / upload_interval #5 minutes rolling average
    filter_values = True
    chunk_size = sampling_rate * upload_interval

    def __init__(self, ws):
        condition = threading.Condition()
        data_box = DataBox(self.chunk_size)
        data_processor = DataProcessor(self.sampling_rate,
                                       self.decimated_sampling_rate,
                                       self.rolling_average_size,
                                       self.filter_values)

        self.data_sampler = DataSampler(condition,
                                        data_box,
                                        self.sampling_rate,
                                        self.upload_interval)

        self.data_uploader = DataUploader(ws,
                                          condition,
                                          data_box,
                                          self.scale_factor,
                                          data_processor)

    def start(self):
        sampler_thread = threading.Thread(target=self.data_sampler.run)
        uploader_thread = threading.Thread(target=self.data_uploader.run)
        sampler_thread.daemon = True
        uploader_thread.daemon = True
        uploader_thread.start()
        sampler_thread.start()


def create_web_api_socket(on_open):
    def on_message(self, ws, message):
        print(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    web_socket_url = "wss://" + \
        os.environ.get('API_ENDPOINT') + "/ws/data-logger"
    auth_token = os.environ.get('AUTH_TOKEN')
    ws = websocket.WebSocketApp(web_socket_url,
                                header=["Authorization:" + auth_token],
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    return ws


def start_seism_logger():
    def on_websocket_open(ws):
        seism_logger = SeismLogger(ws)
        seism_logger.start()

    ws = create_web_api_socket(on_websocket_open)
    ws.run_forever()


if __name__ == "__main__":
    # websocket.enableTrace(True)
    if 'API_ENDPOINT' not in os.environ:
        print("No API_ENDPOINT defined as env var")
    if 'AUTH_TOKEN' not in os.environ:
        print("No AUTH_TOKEN defined as env var")
    else:
        start_seism_logger()
