import board
import displayio
import framebufferio
import rgbmatrix
import adafruit_display_text.label
import terminalio
from adafruit_bitmap_font import bitmap_font
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

now = t0 = time.monotonic_ns()
append_flag = 0


class RGB_Api:
    def __init__(self):

        # Set image
        self.image = "rainbow.bmp"

        # Set text
        self.txt_str_single = "Welcome to our home!"
        self.txt_str = (self.txt_str_single + " ") * 4
        self.txt_color = 0x0F241C
        self.txt_x = 0
        self.txt_y = 32
        self.txt_font = terminalio.FONT
        self.txt_line_spacing = 0.8
        self.txt_scale = 1

        # Set scroll
        self.scroll_speed = 30

        # The following codes don't need to be set
        self.sroll_BITMAP = displayio.OnDiskBitmap(open(self.image, "rb"))
        self.sroll_image1 = displayio.TileGrid(
            self.sroll_BITMAP,
            pixel_shader=getattr(
                self.sroll_BITMAP, "pixel_shader", displayio.ColorConverter()
            ),
            width=1,
            height=1,
            x=0,
            y=0,
            tile_width=self.sroll_BITMAP.width,
            tile_height=self.sroll_BITMAP.height,
        )
        self.sroll_image2 = displayio.TileGrid(
            self.sroll_BITMAP,
            pixel_shader=getattr(
                self.sroll_BITMAP, "pixel_shader", displayio.ColorConverter()
            ),
            width=1,
            height=1,
            x=-self.sroll_BITMAP.width,
            y=-self.sroll_BITMAP.height,
            tile_width=self.sroll_BITMAP.width,
            tile_height=self.sroll_BITMAP.height,
        )
        if self.txt_font == terminalio.FONT:
            self.txt_font = terminalio.FONT
        else:
            self.txt_font = bitmap_font.load_font(self.txt_font)
        self.sroll_text1 = adafruit_display_text.label.Label(
            self.txt_font,
            color=self.txt_color,
            line_spacing=self.txt_line_spacing,
            scale=self.txt_scale,
            text=self.txt_str,
        )
        self.sroll_text1.x = 32
        self.sroll_text1.y = DISPLAY.height // 2
        self.sroll_text2 = adafruit_display_text.label.Label(
            self.txt_font,
            color=self.txt_color,
            line_spacing=self.txt_line_spacing,
            scale=self.txt_scale,
            text=self.txt_str,
        )
        self.sroll_text2.x = -self.sroll_text1.bounding_box[2]
        self.sroll_text2.y = DISPLAY.height // 2

        self.rebound_flag = 0  # Rebound_flag
        self.sroll_object = 0

    # @brief:  Display a text from left to right in horizontal mode
    # @param:  self
    # @retval: None
    def text_right_to_left_horizontal(self):
        global append_flag
        self.sroll_text1.y = DISPLAY.height // 2
        self.sroll_text2.y = DISPLAY.height // 2
        text_length_pixel = self.sroll_text1.bounding_box[2] - self.sroll_text1.bounding_box[0]
        x = self.sroll_text1.x - 1
        if x < - text_length_pixel:
            x = DISPLAY.width
        self.sroll_text1.x = x
        self.sroll_text2.x = -(DISPLAY.width - self.sroll_text1.x)
        if append_flag == 0:
            append_flag = 1
            GROUP.append(self.sroll_text1)
            DISPLAY.show(GROUP)
        time.sleep(1 / self.scroll_speed)


if __name__ == "__main__":
    RGB = RGB_Api()
    GROUP = displayio.Group()
    while True:
        RGB.text_right_to_left_horizontal()
    pass
