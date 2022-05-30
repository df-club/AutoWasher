import time
import mlx90614
import DigitalTube
from machine import I2C, Pin

# I2C mlx90614
SDAPIN = 8
SCLPIN = 9
# 4 bit Digital Tube
SCLKPIN = 5
RCLKPIN = 6
DIOPIN = 7

PUMPPIN = 3

i2c = I2C(scl=Pin(SCLPIN), sda=Pin(SDAPIN), freq=100000)

mlx = mlx90614.MLX90614(i2c)
tube = DigitalTube.DigitalTube(SCLKPIN,RCLKPIN,DIOPIN)
pump = Pin(PUMPPIN, Pin.OUT, value=0)

# def median(data):
#     data.sort()
#     half = len(data) // 2
#     return (data[half] + data[~half])/2

# temp_data_len = 10
# temp_data = [0.0]*temp_data_len
pump_time = 0.8
pump_interval = 1.5

def readTempInDelay(delay_sec):
    readTempInterval = 0.05
    for i in range(int(delay_sec/readTempInterval)):
        tube.setTemp(mlx.read_body_temp(False))
        time.sleep(readTempInterval)

def switch():
    temp = mlx.read_body_temp(False)
    if temp>34 and temp<38:
        # for i in range(temp_data_len):
        #     temp_data[i] = mlx.read_body_temp(False)
        #     time.sleep(0.02)
        # tube.setTemp(median(temp_data))
        pump.value(1)
        readTempInDelay(pump_time)
        # time.sleep(pump_time)
        pump.value(0)
        readTempInDelay(pump_interval)
        # time.sleep(pump_interval)
    else:
        tube.setTemp(0)
        time.sleep(0.5)

if __name__ == '__main__':
    while True: 
        switch()