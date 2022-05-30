import time

class MLX90614():

    _REG_AMBIENT_TEMP = 0x06
    _REG_OBJECT_TEMP = 0x07
    # The address Emissivity contains the object emissivity (factory default 1.0 = 0xFFFF)
    _REG_EMISSIVITY = 0x24
    _REG_EMISSF = 0x2F

    def __init__(self, i2c, address=0x5a):
        self.i2c = i2c
        self.address = address
        self.buf = bytearray(3)

    def read_ambient_temp(self, pec_check=True):
        try:
            t = self.read16(self._REG_AMBIENT_TEMP, crc_check=pec_check)
        except Exception as err:
            raise Exception("Error reading ambient temperature.\n{}".format(err))
        else:
            if (t > 0x7FFF):
                raise Exception("Invalid ambient temperature error.")
            else:
                return (t*0.02 - 273.15)

    def read_object_temp(self, pec_check=True):
        try:
            t = self.read16(self._REG_OBJECT_TEMP, crc_check=pec_check)
        except Exception as err:
            raise Exception("Error reading object temperature.\n{}".format(err))
        else:
            if (t > 0x7FFF):
                raise Exception("Invalid object temperature error.")
            else:
                return (t*0.02 - 273.15)
    
    def read_body_temp(self, pec_check=True):
        TA_LEVEL = 25
        tf_low = tf_high = 0.0
        tbody = 0.0
        ta = self.read_ambient_temp(pec_check)
        tf = self.read_object_temp(pec_check)
        if ta <= TA_LEVEL:
            tf_low = 32.66 + 0.186*(ta-TA_LEVEL)
            tf_high = 34.84 + 0.148*(ta-TA_LEVEL)
        else:
            tf_low  = 32.66 + 0.086*(ta-TA_LEVEL)
            tf_high = 34.84 + 0.1*(ta-TA_LEVEL)
        if tf>=tf_low and tf<=tf_high:
            tbody = 36.3 + 0.5/(tf_high - tf_low)*(tf - tf_low)
        elif tf > tf_high:
            tbody = 36.8 + (0.829321 + 0.002364*ta)*(tf-tf_high)
        elif tf < tf_low:
            tbody = 36.3 + (0.551658 + 0.021525*ta)*(tf-tf_low)
        return tbody

    def _crc8(self, icrc, data):
        crc = icrc ^ data
        for _ in range(8):
            crc <<= 1
            if crc & 0x0100:
                crc ^= 0x07
            crc &= 0xFF
        return crc

    def write16(self, register, data, read_check=True, eeprom_time=50):
        lsb = data & 0x00FF
        msb = data >> 8        
        crc = self._crc8(0, self.address << 1)
        crc = self._crc8(crc, register)
        crc = self._crc8(crc, lsb)
        crc = self._crc8(crc, msb)
        self.buf[0] = lsb; self.buf[1] = msb; self.buf[2] = crc
        self.i2c.writeto_mem(self.address, register, self.buf)
        time.sleep_ms(eeprom_time)
        if read_check:
            try:
                data_read = self.read16(register)
            except Exception as err:
                raise Exception("Error reading after writing to EEPROM register {:02x}.\n{}".format(register, err))
            else:
                if data != data_read:
                    raise Exception("Error reading after writing to EEPROM register {:02x}.\n{}".format(register, err))

    def read16(self, register, crc_check=True):
        self.i2c.readfrom_mem_into(self.address, register, self.buf)
        lsb = self.buf[0]
        msb = self.buf[1]
        pec = self.buf[2]
        crc = 0
        if crc_check:
            crc = self._crc8(crc, self.address << 1)
            crc = self._crc8(crc, register)
            crc = self._crc8(crc, (self.address << 1) + 1)
            crc = self._crc8(crc, lsb)
            crc = self._crc8(crc, msb)
        if (not crc_check) or (pec == crc):
            return lsb | (msb << 8)
        else:
            raise Exception("PEC != CRC8 error in reading register {:02x}.".format(register))
    
    def set_emissivity(self, value=1.0, eeprom_read_check=True, eeprom_write_time=50):
        if (value >= 0) and (value <= 1):
            e_old = self.read16(self._REG_EMISSIVITY,False)
            f_old = self.read16(self._REG_EMISSF,False)
            if value == 1.0:
                e_new = 65535
                f_new = 2458
            else:
                e_new = round(value*65535)
                f_new = round(e_old/e_new*f_old)
            print(e_old, e_new, f_old, f_new)
            
            try:
                time.sleep_ms(eeprom_write_time)
                self.write16(self._REG_EMISSIVITY, 0x0000, read_check=eeprom_read_check, eeprom_time=eeprom_write_time)
                time.sleep_ms(eeprom_write_time)
            except Exception as err:
                raise Exception("Error erasing EEPROM 0x24 emissivity.\n{}".format(err))
            else:
                try:
                    self.write16(self._REG_EMISSIVITY, e_new, read_check=eeprom_read_check, eeprom_time=eeprom_write_time)
                    time.sleep_ms(eeprom_write_time)
                except Exception as err:
                    raise Exception("Error writing EEPROM 0x24 emissivity.\n{}".format(err))
            try:
                time.sleep_ms(eeprom_write_time)
                self.write16(self._REG_EMISSF, 0x0000, read_check=eeprom_read_check, eeprom_time=eeprom_write_time)
                time.sleep_ms(eeprom_write_time)
            except Exception as err:
                raise Exception("Error erasing EEPROM 0x2F emissivity.\n{}".format(err))
            else:
                try:
                    self.write16(self._REG_EMISSF, f_new, read_check=eeprom_read_check, eeprom_time=eeprom_write_time)
                    time.sleep_ms(eeprom_write_time)
                except Exception as err:
                    raise Exception("Error writing EEPROM 0x2F emissivity.\n{}".format(err))
        else:
            raise Exception("Error : emissivity value {} out of range.".format(value))

    def read_emissivity(self, pec_check=True):
        try:
            d = self.read16(self._REG_EMISSIVITY, crc_check=pec_check)
        except Exception as err:
            raise Exception("Error reading emissivity from EEPROM. {}".format(err))
        return d/65535




