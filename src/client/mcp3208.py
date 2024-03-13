# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_MCP3008


class MCP3208(Adafruit_MCP3008.MCP3008):
    # Modification to support the 12 bits ADC
    def read_adc(self, adc_number):
        """Read the current value of the specified ADC channel (0-7).  The values
        can range from 0 to 1023 (10-bits).
        """
        assert 0 <= adc_number <= 7, 'ADC number must be a value of 0-7!'
        # Build a single channel read command.
        # For example channel zero = 0b11000000
        command = 0b11 << 6  # Start bit, single channel read
        command |= (adc_number & 0x07) << 3  # Channel number (in 3 bits)
        # Note the bottom 3 bits of command are 0, this is to account for the
        # extra clock to do the conversion, and the low null bit returned at
        # the start of the response.
        resp = self._spi.transfer([command, 0x0, 0x0])
        # Parse out the 12 bits of response data and return it.
        result = (resp[0] & 0x01) << 11  # only B11 is here
        result |= resp[1] << 3  # B10:B3
        # MSB has B2:B0 ... need to move down to LSB
        result |= resp[2] >> 5
        return (result & 0x0FFF)  # ensure we are only sending 12b
