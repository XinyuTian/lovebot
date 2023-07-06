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


def generate_image_display(image):
    bitmap = displayio.OnDiskBitmap(open(image, "rb"))
    image_display = displayio.TileGrid(
        bitmap,
        pixel_shader=getattr(bitmap, "pixel_shader", displayio.ColorConverter()),
        width=1,
        height=1,
        tile_width=bitmap.width,
        tile_height=bitmap.height,
    )
    return image_display


class Display:
    # Set Text
    text: str = "Welcome to our home! "
    txt_color: int = 0x030B00
    txt_x: int = 0
    txt_y: int = 32
    txt_font: str = terminalio.FONT
    txt_line_spacing: int = 0.8
    txt_scale: int = 1

    # Set Images
    image_idle_active_frames: list = ["images/idle-active-frame-1.bmp", "images/idle-active-frame-2.bmp"]
    image_idle_low_frames: str = ["images/idle-low-frame-1.bmp", "images/idle-low-frame-2.bmp"]
    image_idle_medium_frames: str = ["images/idle-medium-frame-1.bmp", "images/idle-medium-frame-2.bmp"]
    image_idle_high_frames: str = ["images/idle-high-frame-1.bmp", "images/idle-high-frame-2.bmp"]
    image_stim_active_1: str = "images/stim-active-frame-1.bmp"
    image_stim_low_1: str = "images/stim-low-frame-1.bmp"
    image_stim_medium_1: str = "images/stim-medium-frame-1.bmp"
    image_stim_high_1: str = "images/stim-high-frame-1.bmp"
    image_orgasm_frames: list = [
        "images/orgasm-frame-1.bmp",
        "images/orgasm-frame-2.bmp",
        "images/orgasm-frame-3.bmp",
        "images/orgasm-frame-4.bmp",
        "images/orgasm-frame-5.bmp",
        "images/orgasm-frame-6.bmp",
    ]
    image_cooldown_frames: list = ["images/cool-frame-1.bmp", "images/cool-frame-2.bmp"]
    image_height: int = 48
    index_image_alternating: int = 0

    # Set speed
    image_switch_speed = 2
    text_scroll_speed = 30

    @classmethod
    async def display_images_and_text(
        cls,
        state: int = 1,
        progress: str = None,
        stimulation: bool = False,
    ):

        if state == 0:
            group = displayio.Group()
            DISPLAY.show(group)
        elif state == 1:
            group = displayio.Group()
            if stimulation:
                image = getattr(cls, f"image_stim_{progress}_1")
                group.append(generate_image_display(image))
                DISPLAY.show(group)
                time.sleep(0.5)
                DISPLAY.refresh()

            image_displays = [generate_image_display(image) for image in getattr(cls, f"image_idle_{progress}_frames")]
            group.append(image_displays[cls.index_image_alternating])
            cls.index_image_alternating = 1 - cls.index_image_alternating
            DISPLAY.show(group)
            time.sleep(0.5)
            DISPLAY.refresh()
            group.pop()
        else:
            image_displays = [generate_image_display(image) for image in cls.image_orgasm_frames]
            for j in range(4):
                group = displayio.Group()
                for i in range(6):
                    group.append(image_displays[i])
                    DISPLAY.show(group)
                    time.sleep(0.5)
                    DISPLAY.refresh()
                    group.pop()

    def display_animated_images_and_scrolling_text(self, duration=None):
        group = displayio.Group()
        # set the images
        bitmap1_0 = displayio.OnDiskBitmap(open(self.image_loc1_0, "rb"))
        bitmap1_1 = displayio.OnDiskBitmap(open(self.image_loc1_1, "rb"))

        # set the text
        text_length_pixel = self.sroll_text.bounding_box[2] - self.sroll_text.bounding_box[0]
        group.append(self.sroll_text)

        if duration:
            display_starts_at = time.time()

        while True:
            if duration:
                if time.time() - display_starts_at > duration:
                    break
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


if __name__ == "__main__":
    RGB = RGB_display()
    RGB.animate_image_and_scrolling_text()
