import machine
import utime
import network
import gc

import bme280
import ssd1306
import urequests
from prometheus_express import registry, metric

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

i2c = machine.I2C(0, scl=machine.Pin(27, pull=machine.Pin.PULL_UP), sda=machine.Pin(32, pull=machine.Pin.PULL_UP))

display = ssd1306.SSD1306_I2C(128, 64, i2c)

sensor = bme280.BME280_I2C(i2c=i2c)
sensor.set_measurement_settings({
    'filter': bme280.BME280_FILTER_COEFF_OFF,
    'osr_h': bme280.BME280_OVERSAMPLING_1X,
    'osr_p': bme280.BME280_OVERSAMPLING_1X,
    'osr_t': bme280.BME280_OVERSAMPLING_1X})

display.fill(0)
for i, (k, v) in enumerate(sensor.get_measurement_settings().items()):
    display.text(" : ".join((k[:5], str(v))), 0, 10 * i)
display.show()
utime.sleep(5)

# connect to wifi
if not wlan.isconnected():
    wlan.connect('IoTNet', 'IoTNetPW')
    while not wlan.isconnected():
        pass

display.fill(0)
display.text("Wifi connected", 0, 0)
display.show()
utime.sleep(1)

# take reading
sensor.set_power_mode(bme280.BME280_FORCED_MODE)
utime.sleep(1)
measurement = sensor.get_measurement()
display.fill(0)
for i, (k, v) in enumerate(sensor.get_measurement().items()):
    display.text(" : ".join((k[:4], str(v))), 0, 10 * i)
display.show()
utime.sleep(5)

# create metrics
weather_registry = registry.CollectorRegistry(namespace="weatherstation")
temp = metric.Gauge('temperature', '', registry=weather_registry)
temp.set(measurement.get('temperature'))
hum = metric.Gauge('humidity', '', registry=weather_registry)
hum.set(measurement.get('humidity'))
press = metric.Gauge('pressure', '', registry=weather_registry)
press.set(measurement.get('pressure'))

data = "\n".join(weather_registry.render()) + "\n"
del temp, hum, press, weather_registry, measurement

display.fill(0)
display.text("Metrics created", 0, 0)
display.show()
utime.sleep(1)

# send metrics
try:
    request = urequests.post('http://pushgateway.schmalacker.cloud/metrics/job/weatherstation', data=data)
except Exception:
    display.fill(0)
    display.text("Failed request", 0, 0)
    display.show()
    utime.sleep(1)
else:
    display.fill(0)
    display.text("Request made", 0, 0)
    display.text(request.content, 0, 10)
    display.show()
    utime.sleep(1)
    request.close()
    del request

# turn of everything
gc.collect()
display.poweroff()
machine.deepsleep(5 * 60 * 1000)
