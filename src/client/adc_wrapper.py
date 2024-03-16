from typing import Union

import Adafruit_MCP3008

from src.client.adc_config import AdcConfig
from src.client.mcp3208 import MCP3208


class MockAdc(object):

    def read_adc(self, channel: int): return 1


class AdcWrapper(object):
    config: AdcConfig
    adc: Union[Adafruit_MCP3008.MCP3008, MockAdc]

    def __init__(self, config: AdcConfig):
        self.config = config

        if config.mock_adc:
            self.adc = MockAdc()
            return

        if config.adc_bit_resolution == 12:
            self.adc = MCP3208(
                clk=config.CLK,
                cs=config.CS,
                miso=config.MISO,
                mosi=config.MOSI
            )
        elif config.adc_bit_resolution == 10:
            self.adc = Adafruit_MCP3008.MCP3008(
                clk=config.CLK,
                cs=config.CS,
                miso=config.MISO,
                mosi=config.MOSI
            )
        else:
            print("Unsupported resolution provided to AdcWrapper")

    def supports_bias_point_measurement(self) -> bool:
        return self.config.bias_point_channel is not None

    def _read_adc(self, channel: int) -> int:
        value = self.adc.read_adc(channel)
        if value == 0 or value == 2 ** self.config.adc_bit_resolution - 1:
            print("Read invalid value:", value)
            return -1
        else:
            return value

    def read_coil(self) -> int:
        return self._read_adc(self.config.coil_input_channel)

    def read_bias_point(self) -> int:
        return self._read_adc(self.config.bias_point_channel)
