from machine import Pin, Timer

class DigitalTube:
    #  0	 1	  2	   3	4	 5	  6	   7	8	 9	  A	   b	C    d	  E    F    -    None
    _SEGMENTS = (0xC0, 0xF9, 0xA4, 0xB0, 0x99, 0x92, 0x82, 0xF8, 0x80,
                 0x90, 0x8C, 0xBF, 0xC6, 0xA1, 0x86, 0xFF, 0xbf, 0xff)
    temp = 0.0

    def __init__(self, SCLKPin, RCLKPin, DIOPin):
        self.sclk = Pin(SCLKPin, Pin.OUT)
        self.rclk = Pin(RCLKPin, Pin.OUT)
        self.dio = Pin(DIOPin, Pin.OUT)
        tim = Timer(0)
        tim.init(period=2, mode=Timer.PERIODIC, callback=lambda x: self.showTemp())


    def LED_OUT(self, x):
        for i in range(8):
            if x & 0x80:
                self.dio.value(1)
            else:
                self.dio.value(0)
            x <<= 1  # 二进制左移，等同于 x=x*2
            self.sclk.value(0)
            self.sclk.value(1)
    
    # position can be set as 0x01,0x02,0x04,0x08 of the 4 bit LED segment 
    def selLEDShow(self, SEGID, position):
        self.LED_OUT(self._SEGMENTS[SEGID])
        self.LED_OUT(position)
        self.rclk.value(0)
        self.rclk.value(1)
    
    def selLEDShowWithDot(self, SEGID, position):
        self.LED_OUT(self._SEGMENTS[SEGID] & 0x7f)
        self.LED_OUT(position)
        self.rclk.value(0)
        self.rclk.value(1)

    def showTemp(self):
        t = self.temp * 10
        self.selLEDShow(int(t%10),0x01)
        t = t/10
        self.selLEDShowWithDot(int(t%10),0x02)
        t = t/10
        self.selLEDShow(int(t%10),0x04)
        self.selLEDShow(17,0x01)
        self.selLEDShow(17,0x02)
        self.selLEDShow(17,0x04)

    def setTemp(self, temp):
        self.temp = temp
