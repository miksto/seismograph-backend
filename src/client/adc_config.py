from src.shared.Constants import SEISMOMETER_ID_LEHMAN, SEISMOMETER_ID_VERTICAL_PENDULUM


class AdcConfig(object):
    def __init__(self, seismometer_id):
        if seismometer_id == SEISMOMETER_ID_LEHMAN:
            self.bias_point_channel = None
            self.coil_input_channel = 7
            self.adc_bit_resolution = 10
            self.CLK = 12
            self.MISO = 16
            self.MOSI = 20
            self.CS = 21
        elif seismometer_id == SEISMOMETER_ID_VERTICAL_PENDULUM:
            self.bias_point_channel = None
            self.coil_input_channel = 0
            self.adc_bit_resolution = 12
            self.CLK = 18
            self.MISO = 23
            self.MOSI = 24
            self.CS = 25
        else:
            raise print("Invalid seismometer_id provided to AdcConfig")
