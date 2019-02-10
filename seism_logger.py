import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import json
import random
import datetime

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
    desired_freq = 1.4
    desired_freq_nyk = desired_freq * 2
    wn = desired_freq_nyk / sampling_rate
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
    def run(*args):
        sample_rate = 300
        chunk_size = sample_rate * 10
        sleep_time = 1/(sample_rate/0.8)
        avg_list = [0] * (sample_rate * 60)
        data_box = DataBox(sample_rate, chunk_size)

        while True:
            val_count = 0
            for k in avg_list:
                if k != 0:
                    val_count += 1

            rolling_avg = sum(avg_list) / val_count if val_count > 0 else mcp.read_adc(2)
            while not data_box.isFull():
                value = mcp.read_adc(2)
                adj_value = value - rolling_avg
                data_box.add(adj_value)
                
                if not data_box.isFull():
                    time.sleep(sleep_time)

                avg_list.pop(0)
                avg_list.append(value)

            values = data_box.get_filtered_values()
            int_values = np.rint(values*4)
            t1 = datetime.datetime.now()
            data = '{"values": ' + json.dumps(int_values.tolist()) + ', "type": "post_data"}'
            ws.send(data)
            t2 = datetime.datetime.now()
            adjusted_sleep_time = sleep_time - (t2-t1).total_seconds()
            if adjusted_sleep_time > 0:
                time.sleep(adjusted_sleep_time)

        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())

if __name__ == "__main__":
    #websocket.enableTrace(True)
    while True:
        try:
            ws = websocket.WebSocketApp("ws://128.199.197.181:3000",
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
            ws.on_open = on_open
            ws.run_forever()
            # Sleep 5 seconds before each attempt to reconnect
            time.sleep(5)
        except Exception as e:
            print(e)
