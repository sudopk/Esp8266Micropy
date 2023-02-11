import time
import os
import machine
import json
import uasyncio

from lib import config_lib
from lib import relay_lib
from lib import wifi_lib


wifi_lib.info()

async def web_server_loop():
  server = wifi_lib.WebServer()
  try:
    while True:
      try:
        server.process_request()
        await uasyncio.sleep_ms(50)
      except Exception as e:
        print(f'Request failed with {e}')
  finally:
    server.close()

async def welder_loop():
  while True:
    for _ in range(3):
      # Low turns on the led
      relay_lib.led_builtin_pin.off()
      await uasyncio.sleep_ms(100)
      # High turns off the led
      relay_lib.led_builtin_pin.on()
      await uasyncio.sleep_ms(100)


    await uasyncio.sleep_ms(500)

    for _ in range(2):
      relay_lib.led_builtin_pin.off()
      await uasyncio.sleep_ms(100)
      relay_lib.led_builtin_pin.on()
      await uasyncio.sleep_ms(100)


    await uasyncio.sleep_ms(500)

    relay_lib.led_builtin_pin.off()
    await uasyncio.sleep_ms(100)

    relay_lib.relay_pin.on()
    config = config_lib.load_config()
    await uasyncio.sleep_ms(config[config_lib.PULSE_MS_KEY])
    relay_lib.relay_pin.off()
    relay_lib.led_builtin_pin.on()

    await uasyncio.sleep(3)


async def main():
  ws_task = uasyncio.create_task(web_server_loop())
  weld_task = uasyncio.create_task(welder_loop())
  await ws_task
  await weld_task



uasyncio.run(main())

# relay_lib.try_relay()


