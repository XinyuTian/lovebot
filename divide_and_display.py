import board
import displayio
import framebufferio
import rgbmatrix
import time
import terminalio
from adafruit_bitmap_font import bitmap_font
import adafruit_display_text.label

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

DISPLAY = framebufferio.FramebufferDisplay(matrix, auto_refresh=True, rotation=180)


class RGB_Api:
    def __init__(
        self,
        image_1="smiley_0.bmp",
        image_2="smiley_1.bmp",
        text="Welcome to our home!",
    ):
        # Set images
        self.image_loc1_0 = image_1
        self.image_loc1_1 = image_2
        self.image_loc1_number = 0

        # Set text
        self.txt_str_single = text
        self.txt_str = (self.txt_str_single + " ") * 4
        self.txt_color = 0x030B00
        self.txt_x = 0
        self.txt_y = 32
        self.txt_font = terminalio.FONT
        self.txt_line_spacing = 0.8
        self.txt_scale = 1

        # Set speed
        self.switch_speed = 2
        self.scroll_speed = 30
        self.scroll_steps_per_switch = self.scroll_speed // self.switch_speed

        # Set division
        self.image_height = 48

        # The following codes don't need to be set
        if self.txt_font == terminalio.FONT:
            self.txt_font = terminalio.FONT
        else:
            self.txt_font = bitmap_font.load_font(self.txt_font)
        self.sroll_text = adafruit_display_text.label.Label(
            self.txt_font,
            color=self.txt_color,
            line_spacing=self.txt_line_spacing,
            scale=self.txt_scale,
            text=self.txt_str,
        )
        self.sroll_text.x = unit_width // 2
        self.sroll_text.y = (unit_height + self.image_height) // 2

    def animate_image_and_scrolling_text(self):
        group = displayio.Group()
        # set the images
        bitmap1_0 = displayio.OnDiskBitmap(open(self.image_loc1_0, "rb"))
        bitmap1_1 = displayio.OnDiskBitmap(open(self.image_loc1_1, "rb"))

        # set the text
        text_length_pixel = self.sroll_text.bounding_box[2] - self.sroll_text.bounding_box[0]
        group.append(self.sroll_text)

        while True:
            # update the image
            self.image_loc1_number = 1 - self.image_loc1_number
            if self.image_loc1_number == 0:
                bitmap1 = bitmap1_0
            else:
                bitmap1 = bitmap1_1
            group.append(
                displayio.TileGrid(
                    bitmap1,
                    pixel_shader=getattr(bitmap1, "pixel_shader", displayio.ColorConverter()),
                    width=1,
                    height=1,
                    tile_width=bitmap1.width,
                    tile_height=bitmap1.height,
                    x=0,
                    y=0,
                )
            )

            # update the text
            for i in range(self.scroll_steps_per_switch):
                x = self.sroll_text.x - 1
                if x < -text_length_pixel:
                    x = DISPLAY.width // 2
                self.sroll_text.x = x

                time.sleep(1 / self.scroll_speed)

            DISPLAY.show(group)
            DISPLAY.refresh()
        pass
