from machine import Pin, ADC
from time import sleep

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)  # Full range: 3.3v

while True:
    print(f"{pot.read()} - {pot.read_u16()} - {pot.read_uv() / (1000*1000)}")
    sleep(0.1)
