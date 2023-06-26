import board
import digitalio
import time

counter = 0
debounce_time = 0

pin = digitalio.DigitalInOut(board.GP15)
pin.switch_to_input(pull=digitalio.Pull.UP)

while True:
    if not pin.value and (time.monotonic() - debounce_time) > 0.3:
        counter += 1
        debounce_time = time.monotonic()
        print("Button Pressed")
        print("Count={}".format(counter))