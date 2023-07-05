import board
import displayio
import framebufferio
import rgbmatrix
import time

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

    def static_image(self):
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
            time.sleep(0.5)
            group.append(bitmap2_display)
            DISPLAY.show(group)
            DISPLAY.refresh()
            time.sleep(0.5)
            #
        pass


if __name__ == "__main__":
    RGB = RGB_Api()
    group = displayio.Group()
    RGB.static_image()
