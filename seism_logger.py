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
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

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
        sample_rate = 60
        sleep_time = 1/sample_rate
        buffer_size = 20
        buffer = [0] * buffer_size

        while True:
            
            for i in range(0, buffer_size):
                tmp_value_sum = 0
                for j in range(0, sample_avg_count):
                    tmp_value_sum += mcp.read_adc(0)
                    if j < sample_avg_count-1:
                        time.sleep(sleep_time)
                avg_value = tmp_value_sum / sample_avg_count
                buffer[i] = avg_value

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

