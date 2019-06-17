import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import json
import random
import datetime
import os

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

import sys
from scipy import signal
import numpy as np

# Software SPI configuration:
CLK  = 18
MISO = 23
MOSI = 24
CS   = 25

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
        result |= resp[2] >> 5           # MSB has B2:B0 ... need to move down to LSB
        return (result & 0x0FFF)  # ensure we are only sending 12b

class DataFilter(object):
  zi = None
  b = None
  a = None

  def __init__(self, sampling_rate):
    self.sampling_rate = sampling_rate
    nyquist_freq = sampling_rate / 2
    filter_cutoff_freq = 1.4 #Hz
    wn = filter_cutoff_freq / nyquist_freq

    self.b, self.a = signal.butter(4, wn)
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
      self._avg_list.pop(0)
  
  def add(self, value):
    self._avg_list.append(value)
    self._trim_size()

  def is_empty(self):
    return not self._avg_list

  def get_average(self):
    current_size = len(self._avg_list)
    if current_size > 0:
      return sum(self._avg_list) / current_size
    else:
      return 0


class DataBox(object):
  max_size = 0
  decimation_factor = 0
  data = []
  filter = None

  def __init__(self, sampling_rate, max_size):
    target_sampling_rate = 15
    self.decimation_factor = sampling_rate // target_sampling_rate
    self.max_size = max_size
    self.filter = DataFilter(sampling_rate)

  def add(self, data_point):
    self.data.append(data_point)

  def isFull(self):
    return len(self.data) >= self.max_size

  def get_filtered_values(self):
    filtered_data = self.filter.process(self.data)
    decimated_data = signal.decimate(filtered_data, self.decimation_factor)
    self.data = []
    return decimated_data

  def get_unfiltered_values(self):
    decimated_data = signal.decimate(self.data, self.decimation_factor)
    self.data = []
    return decimated_data

class DataSampler(object):

  def __init__(self, sample_rate=500, upload_interval=10, rolling_avg_minutes=2, filter=True, on_batch_full=None):
    avg_list_size = sample_rate * rolling_avg_minutes * 60
    chunk_size = sample_rate * upload_interval
    
    self.filter_data = filter
    self.on_batch_full = on_batch_full
    self.sleep_time = 1/(sample_rate/0.2)
    self.data_box = DataBox(sample_rate, chunk_size)
    self.rolling_avg = RollingAverage(avg_list_size)

  def run(self):
    #Init avg with a real value
    self.rolling_avg.add(mcp.read_adc(2))

    while True:
        rolling_avg = self.rolling_avg.get_average()
        while not self.data_box.isFull():
            value = mcp.read_adc(2)
            adjusted_value = value - rolling_avg
            self.data_box.add(adjusted_value)
            self.rolling_avg.add(value)
            
            if not self.data_box.isFull():
                time.sleep(self.sleep_time)

        t1 = datetime.datetime.now()
        if self.filter_data:
          values = self.data_box.get_filtered_values()
        else:
          values = self.data_box.get_unfiltered_values()

        self.on_batch_full(values)
        t2 = datetime.datetime.now()
        adjusted_sleep_time = self.sleep_time - (t2-t1).total_seconds()
        if adjusted_sleep_time > 0:
            time.sleep(adjusted_sleep_time)

class SeismLogger(object):

  def __init__(self, ws):
    self.ws = ws
    self.data_sampler = DataSampler(upload_interval=10, filter=True, on_batch_full=self.on_batch_full)

  def upload_data(self, values):
      int_values = np.rint(values*2)
      data = '{"values": ' + json.dumps(int_values.tolist()) + ', "type": "post_data"}'
      self.ws.send(data)

  def on_batch_full(self, values):
    self.upload_data(values)
  
  def run(self, *args):
    self.data_sampler.run()
    self.ws.close()
    print("thread terminating...")


mcp = MCP3208(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
current_millis = lambda: int(round(time.time() * 1000))

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")
    seism_logger = SeismLogger(ws)
    thread.start_new_thread(seism_logger.run, ())

def main_loop():
    while True:
        try:
            auth_token = os.environ.get('AUTH_TOKEN')
            web_socket_url = "wss://" + os.environ.get('API_ENDPOINT') + "/ws/data-logger"
            ws = websocket.WebSocketApp(web_socket_url,
                                    header=["Authorization:" + auth_token],
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
            ws.on_open = on_open
            ws.run_forever()
            # Sleep 5 seconds before each attempt to reconnect
            time.sleep(5)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    #websocket.enableTrace(True)
    if 'API_ENDPOINT' not in os.environ:
        print("No API_ENDPOINT defined as env var")
    if 'AUTH_TOKEN' not in os.environ:
        print("No AUTH_TOKEN defined as env var")
    else: 
        main_loop()
