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

import sys, signal

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
        sample_avg_count = 6
        sample_rate = 90
        sleep_time = 1/sample_rate
        # 2 seconds worth of data
        buffer_size = int(sample_rate/sample_avg_count) * 2
        buffer = [0] * buffer_size
        avg_list = [0] * (buffer_size * 60) # 2 minutes

        while True:
            val_count = 0
            for k in avg_list:
                if k != 0:
                    val_count += 1
            
            rolling_avg = sum(avg_list) / val_count if val_count > 0 else 2000
            for i in range(0, buffer_size):
                tmp_value_sum = 0
                for j in range(0, sample_avg_count):
                    tmp_value_sum += mcp.read_adc(2)
                    if j < sample_avg_count-1:
                        time.sleep(sleep_time)
                avg_value = tmp_value_sum / sample_avg_count
                buffer[i] = round((avg_value - rolling_avg) * 8)

                avg_list.pop(0)
                avg_list.append(avg_value)

            t1 = datetime.datetime.now()
            data = '{"values": ' + json.dumps(buffer) + ', "type": "post_data"}'
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
