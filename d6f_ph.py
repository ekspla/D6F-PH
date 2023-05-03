#coding:utf-8
#
# (c) 2023 ekspla.
# MIT license.  https://github.com/ekspla/D6F-PH
"""A micropython module for differential pressure sensor, D6F-PH (OMRON).
"""

from time import sleep_ms

class D6F_PH:
    """
    I2C driver for D6F-PH pressure sensor (OMRON)
    """

    _I2C_ADDRESS = 0x6c
    # Specific Model of D6F-PH
    # e.g. for model 5050
    # Where:
    # the pressure range is from -500 to +500 Pa
    _PRESSURE_RANGE = {
        '0505': 100, # +/- 50 Pa
        '0025': 250, # 0-250 Pa
        '5050': 1000, # +/- 500 Pa
    }

    # Pressure transfer function per Datasheet
    def _PRESSURE_MODE_P(self, output_decimal):
        return (output_decimal - 1024) * self._pres_range / 60000

    def _PRESSURE_MODE_PN(self, output_decimal):
        return (output_decimal - 1024) * self._pres_range / 60000 - self._pres_range / 2

    # Temperature transfer function per Datasheet
    @staticmethod
    def _temp_celsius(output_decimal):
        return (output_decimal - 10214) * 100 / 3739 # // convert to degree-C

    def __init__(self, i2c_obj, address=_I2C_ADDRESS, pressure_range='5050', en_crc=False, offset=0):
        """
        :param i2c_obj: I2C class; I2C bus
        :param address: int; Sensor I2C address, pls refer to the datasheet
        :param pressure_range: int or str; Sensor pressure range, pls refer to the datasheet
        :param en_crc: True/False; enable/disable crc8 for data validation
        :param offset: int; pressure offset in raw decimal
        """
        self._i2c = i2c_obj
        self._addr = address
        if isinstance(pressure_range, str):
            self._pres_range = self._get_pres_range(pressure_range)
        else:
            self._pres_range = pressure_range
        self._pres_func = self._get_pres_func(self._pres_range)
        self._offset = offset

        self._i2c.writeto(address, b'\x0b\x00') # /* EEPROM Control <= 00h */
        if en_crc:
            self.en_crc = True
            self._i2c.writeto(address, b'\x00\xd0\x49\x18\x02') # /* [D049] <= 02h */
            self._buffer = bytearray(3) # 2-byte data and 1-byte crc
        else:
            self.en_crc = False
            self._buffer = bytearray(2) # 2-byte data

    def _get_pres_func(self, pres_range):
        if isinstance(pres_range, int):
            if pres_range == 250:
                func = '_PRESSURE_MODE_P'
            elif pres_range in (100, 1000):
                func = '_PRESSURE_MODE_PN'
            return getattr(self, func)
        else:
            raise Exception('Error: Incorrect pressure range.')

    def _get_pres_range(self, pressure_range):
        if isinstance(pressure_range, str):
            if pressure_range in self._PRESSURE_RANGE:
                return self._PRESSURE_RANGE.get(pressure_range)
        else:
            raise Exception('Error: Incorrect pressure range setting.')

    def crc8(self, byte_array, poly=0x131, init=0x00): # Polynomial: x^8 + x^5 + x^4 + x^0
        """
        Calculate CRC8-Dallas/Maxim
        :param byte_array: bytes or bytearray; sensor data
        :return: int; crc8
        """
        crc = init
        for byte in byte_array:
            crc ^= byte
            for _ in range(8):
                crc = (crc << 1) ^ poly if crc & 0x80 else crc << 1
            crc &= 0xff
        return crc ^ 0x00

    def read_raw(self):
        """
        Read raw decimal output
        :return: tuple(int, int); raw pressure decimal output, raw temperature decimal output
        """
        self._i2c.writeto(self._addr, b'\x00\xd0\x40\x18\x06') # /* [D040] <= 06h */
        sleep_ms(33)

        self._i2c.writeto(self._addr, b'\x00\xd0\x51\x2c') # /* [D051/D052] => Read COMP_DATA1_H/COMP_DATA1_L values */
        self._i2c.readfrom_mem_into(self._addr, 0x07, self._buffer)
        #print(self._buffer)
        if self.en_crc and ((crc := self.crc8(self._buffer[:2])) != self._buffer[2]):
            print(self._buffer, hex(crc))
            return None
        raw_pres = int.from_bytes(self._buffer[:2], 'big') - self._offset # Covert from 2-byte BE unsigned int.

        self._i2c.writeto(self._addr, b'\x00\xd0\x61\x2c') # /* [D061/D062] => Read TMP_H/TMP_L values */
        self._i2c.readfrom_mem_into(self._addr, 0x07, self._buffer)
        #print(self._buffer)
        if self.en_crc and ((crc := self.crc8(self._buffer[:2])) != self._buffer[2]):
            print(self._buffer, hex(crc))
            return None
        raw_temp = int.from_bytes(self._buffer[:2],'big') # Covert from 2-byte BE unsigned int.

        return raw_pres, raw_temp

    def read(self):
        """
        Read pressure in Pa & temperature in degree Celsius
        :return: tuple(float, float); pressure reading in Pa, temperature reading in degree Celsius
        """
        if not (raw_counts := self.read_raw()):
            return None
        raw_pres, raw_temp = raw_counts
        temp = self._temp_celsius(raw_temp)
        pres = self._pres_func(raw_pres)
        return pres, temp

    def read_pa(self):
        """
        Read pressure in Pa
        :return: float;
        """
        pa, _ = self.read()
        return pa

    def read_psi(self):
        """
        Read pressure in PSI
        :return: float;
        """
        return self.read_pa() / 6894.75729

    def read_hpa(self):
        """
        Read pressure in hPa
        :return: float;
        """
        return self.read_pa() / 100

    def read_temp_c(self):
        """
        Read temperature in degree Celsius
        :return: float;
        """
        _, temp = self.read()
        return temp

    def read_temp_f(self):
        """
        Read temperature in Fahrenheit
        :return: float
        """
        return self.read_temp_c() * 1.8 + 32