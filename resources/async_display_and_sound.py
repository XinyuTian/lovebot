# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
CircuitPython single MP3 playback example for Raspberry Pi Pico.
Plays a single MP3 once.
"""
import board
import audiomp3
import audiopwmio

import displayio
import framebufferio
import rgbmatrix
import time
import asyncio

bit_depth_value = 6
unit_width = 64
unit_height = 64
chain_width = 1
chain_height = 1
serpentine_value = True

width_value = unit_width * chain_width
height_value = unit_height * chain_height

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=width_value,
    height=height_value,
    bit_depth=bit_depth_value,
    rgb_pins=[board.GP2, board.GP3, board.GP4, board.GP5, board.GP8, board.GP9],
    addr_pins=[board.GP10, board.GP16, board.GP18, board.GP20, board.GP22],
    clock_pin=board.GP11,
    latch_pin=board.GP12,
    output_enable_pin=board.GP13,
    tile=chain_height,
    serpentine=serpentine_value,
    doublebuffer=True,
)

# https://docs.circuitpython.org/en/latest/shared-bindings/framebufferio/index.html#framebufferio.FramebufferDisplay
DISPLAY = framebufferio.FramebufferDisplay(matrix, auto_refresh=True, rotation=180)


class RGB_Api:
    def __init__(self):
        # Set image
        self.image1 = "images/idle-high-frame-1.bmp"
        self.image2 = "images/idle-high-frame-2.bmp"

    async def static_image(self):
        group = displayio.Group()
        bitmap1 = displayio.OnDiskBitmap(open(self.image1, "rb"))
        bitmap2 = displayio.OnDiskBitmap(open(self.image2, "rb"))
        bitmap_display = displayio.TileGrid(
            bitmap1,
            pixel_shader=getattr(bitmap1, 'pixel_shader', displayio.ColorConverter()),
            width=1,
            height=1,
            tile_width=bitmap1.width,
            tile_height=bitmap1.height,
        )

        bitmap2_display = displayio.TileGrid(
            bitmap2,
            pixel_shader=getattr(bitmap2, 'pixel_shader', displayio.ColorConverter()),
            width=1,
            height=1,
            tile_width=bitmap2.width,
            tile_height=bitmap2.height,
        )
        group.append(bitmap_display)
        group.append(bitmap2_display)

        while True:
            group.pop()
            DISPLAY.show(group)
            DISPLAY.refresh()
            await asyncio.sleep(0.5)
            group.append(bitmap2_display)
            DISPLAY.show(group)
            DISPLAY.refresh()
            await asyncio.sleep(0.5)
            #
        pass


async def play_sound():
    audio = audiopwmio.PWMAudioOut(board.GP0)

    decoder = audiomp3.MP3Decoder(open("beeps.mp3", "rb"))

    audio.play(decoder)
    while audio.playing:
        pass
    await asyncio.sleep(0.1)
    print("Done playing!")


async def main():
    RGB = RGB_Api()
    display_task = asyncio.create_task(RGB.static_image())
    sound_task = asyncio.create_task(play_sound())
    await asyncio.gather(
        sound_task,
        display_task,
    )


asyncio.get_event_loop().run_until_complete(main())

