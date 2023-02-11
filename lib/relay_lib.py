import machine
import time

RELAY_PIN = 4
LED_BUILTIN = 2

relay_pin = machine.Pin(RELAY_PIN, machine.Pin.OUT)
led_builtin_pin = machine.Pin(LED_BUILTIN, machine.Pin.OUT)

RELAY_DELAY_MS = 100

def try_relay():
    print(f'Turning pin on: {relay_pin.value()}')
    relay_pin.on()
    time.sleep_ms(RELAY_DELAY_MS)
    print(f'Turning pin off: {relay_pin.value()}')
    relay_pin.off()
    time.sleep_ms(RELAY_DELAY_MS)

def is_relay_on() -> bool:
    return relay_pin.value() != 0


