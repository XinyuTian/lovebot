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

width_value = unit_width*chain_width
height_value = unit_height*chain_height

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=width_value, height=height_value, bit_depth=bit_depth_value,
    rgb_pins=[board.GP2, board.GP3, board.GP4, board.GP5, board.GP8, board.GP9],
    addr_pins=[board.GP10, board.GP16, board.GP18, board.GP20, board.GP22],
    clock_pin=board.GP11, latch_pin=board.GP12, output_enable_pin=board.GP13,
    tile=chain_height, serpentine=serpentine_value,
    doublebuffer=True)

# https://docs.circuitpython.org/en/latest/shared-bindings/framebufferio/index.html#framebufferio.FramebufferDisplay
DISPLAY = framebufferio.FramebufferDisplay(matrix, auto_refresh=True,rotation=180)


class RGB_Api():
    def __init__(self):
        #Set image
        self.image = 'frame_1.bmp'
        self.image2 = 'frame_2.bmp'

    #@brief:  Display an image in static mode
    def static_image(self, image):
        bitmap = displayio.OnDiskBitmap(open(image, 'rb'))
        group.append(
            displayio.TileGrid(
                bitmap,
                pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter()),
                width=1,
                height=1,
                tile_width=bitmap.width,
                tile_height=bitmap.height,
            )
        )

        DISPLAY.show(group)
        DISPLAY.refresh()


if __name__ == '__main__':
    RGB = RGB_Api()
    group = displayio.Group()
    while True:
        RGB.static_image(RGB.image)
        time.sleep(0.5)
        RGB.static_image(RGB.image2)
        time.sleep(0.5)
    pass
