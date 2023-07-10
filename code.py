import asyncio
import board
import keypad
import displayio
import framebufferio
import rgbmatrix
import time
import terminalio
import adafruit_display_text.label
import array
import math
import audiocore
import audiobusio

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


class Stimulation:
    def __init__(self, button_number, received_at):
        self.button_number = button_number
        self.received_at = received_at


class Button:
    def __init__(self, name, number, pin):
        self.name = name
        self.number = number
        self.pin = pin


ordered_button_numbers = [0, 1, 2]

left_button_stroke_names = ["LEFT_1", "LEFT_2", "LEFT_3"]
button_l_1 = Button(left_button_stroke_names[0], 0, board.GP21)
button_l_2 = Button(left_button_stroke_names[1], 1, board.GP19)
button_l_3 = Button(left_button_stroke_names[2], 2, board.GP17)

right_button_stroke_names = ["RIGHT_1", "RIGHT_2", "RIGHT_3"]
button_r_1 = Button(right_button_stroke_names[0], 0, board.GP28)
button_r_2 = Button(right_button_stroke_names[1], 1, board.GP27)
button_r_3 = Button(right_button_stroke_names[2], 2, board.GP26)


def categorize_session_progress(progress_percentage):
    categories = {(0, 10): "active", (10, 33): "low", (33, 66): "medium", (66, 100): "high"}
    for interval, category in categories.items():
        if interval[0] <= progress_percentage < interval[1]:
            return category
    return "high"


class Session:
    stimulation_log: list = []
    strokes_goal: int = 60
    velocity_goal: int = 3
    stimulation_evaluation_pointer: int = 0
    stroke_count: int = 0
    session_started_at: timestamp
    session_succeeded_at: timestamp
    state: int = 0  # 0 - idel; 1 - operating; 2 - success
    progress: str = "active"
    stimulation: bool = False

    @classmethod
    async def detect_upto_one_stroke(cls):
        i = cls.stimulation_evaluation_pointer
        j = 0  # ordered_button_numbers_pointer
        stroke_starts_from = i
        while i < len(cls.stimulation_log) and j <= 2:
            if cls.stimulation_log[i].button_number == 0:
                stroke_starts_from = i
                i += 1
                j = 1
                continue
            if cls.stimulation_log[i].button_number == ordered_button_numbers[j]:
                j += 1
            elif cls.stimulation_log[i].button_number == ordered_button_numbers[j - 1]:
                pass
            else:
                stroke_starts_from = i
            i += 1
        if (
            j == 3
            and cls.stimulation_log[i - 1].received_at - cls.stimulation_log[stroke_starts_from].received_at
            < cls.velocity_goal
        ):
            cls.stroke_count += 1
            cls.stimulation_evaluation_pointer = i
            cls.progress = categorize_session_progress(cls.stroke_count / cls.strokes_goal * 100)
            if cls.stroke_count < cls.strokes_goal:
                Session.stimulation = True
        if len(Session.stimulation_log) > 110:
            cls.stimulation_log = cls.stimulation_log[100:]
            cls.stimulation_evaluation_pointer -= 100

    @classmethod
    async def update_state(cls):
        if cls.state == 0:  # idle
            if cls.stimulation_log == []:
                pass
            elif time.time() - cls.stimulation_log[-1].received_at < 1:
                cls.state = 1
                cls.progress = "active"
                cls.stimulation_log = [cls.stimulation_log[-1]]
                cls.stroke_count = 0
                cls.stimulation_evaluation_pointer = 0
        elif cls.state == 1:  # active
            if cls.stroke_count >= cls.strokes_goal:
                cls.session_succeeded_at = time.time()
                cls.state = 2
            elif time.time() - cls.stimulation_log[-1].received_at > 30:
                cls.state = 0
        elif cls.state == 2:  # success + cooldown
            await asyncio.sleep(20)
            cls.state = 3
            await asyncio.sleep(20)
            cls.state = 0
            cls.stimulation_log = [cls.stimulation_log[-1]]
            cls.stimulation_evaluation_pointer = 0
        print(f"Left strokes: {cls.stroke_count}; state: {cls.state}")


async def stimulator(button):
    """Print a message when pin goes low and when it goes high."""
    with keypad.Keys((button.pin,), value_when_pressed=False) as keys:
        while True:
            event = keys.events.get()
            if event:
                if event.pressed:
                    stimulation = Stimulation(button.number, time.time())
                    Session.stimulation_log.append(stimulation)
                    print(stimulation.button_number, stimulation.received_at, len(Session.stimulation_log))
            await asyncio.sleep(0.1)


async def orchestrator():
    while True:
        await Session.detect_upto_one_stroke()
        await Session.update_state()
        await asyncio.sleep(0.5)


async def beeper():
    audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP15)
    # mp3 = audiomp3.MP3Decoder(open("beep.mp3", "rb"))
    tone_volume = 0.1  # Increase this to increase the volume of the tone.
    frequency = 440  # Set this to the Hz of the tone you want to generate.
    length = 8000 // frequency
    sine_wave = array.array("h", [0] * length)
    for i in range(length):
        sine_wave[i] = int((math.sin(math.pi * 2 * i / length)) * tone_volume * (2**15 - 1))
    sine_wave_sample = audiocore.RawSample(sine_wave)

    while True:
        await asyncio.sleep(0.5)
        if Session.stimulation == True:
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.2)
            audio.stop()
            # audio.play(mp3)
        elif Session.state == 2:
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.1)
            audio.stop()
            await asyncio.sleep(0.1)
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.1)
            audio.stop()
            await asyncio.sleep(0.1)
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.1)
            audio.stop()
            await asyncio.sleep(0.1)
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.1)
            audio.stop()
            await asyncio.sleep(0.1)
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.1)
            audio.stop()
            await asyncio.sleep(0.1)
            audio.play(sine_wave_sample, loop=True)
            await asyncio.sleep(0.1)
            audio.stop()
            await asyncio.sleep(0.1)


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
    text_categories = {
        (
            1,
            "active",
        ): "STROKE MY BUTTONS BOT WANT PLEASURE STROKE MY BUTTONS BOT WANT PLEASURE STROKE MY BUTTONS BOT WANT PLEASURE",
        (
            1,
            "low",
        ): "YES JUST LIKE THAT BOT WANTS MORE YES JUST LIKE THAT BOT WANTS MORE YES JUST LIKE THAT BOT WANTS MORE",
        (
            1,
            "medium",
        ): "BOT IS HAPPY KEEP GOING PLZ BOT IS HAPPY KEEP GOING PLZ BOT IS HAPPY KEEP GOING PLZ BOT IS HAPPY KEEP GOING PLZ",
        (
            1,
            "high",
        ): "AHH~ AHH~ BOT HAPPY AHH~ AHH~ BOT HAPPY AHH~ AHH~ BOT HAPPY AHH~ AHH~ BOT HAPPY AHH~ AHH~ BOT HAPPY AHH~ AHH~ BOT HAPPY ",
        (
            2,
            "high",
        ): "OMG <3 OMG <3 OMG <3 OMG <3 OMG OMG <3 OMG <3 OMG <3 OMG <3 OMG OMG <3 OMG <3 OMG <3 OMG <3 OMG OMG <3 OMG <3 OMG <3 OMG <3 OMG ",
        (
            3,
            "high",
        ): "BOT IS TIRED... LEAVE BOT ALONE... BOT IS TIRED... LEAVE BOT ALONE... BOT IS TIRED... LEAVE BOT ALONE... BOT IS TIRED... LEAVE BOT ALONE...",
    }

    text_categories_ptrs = {
        (1, "active"): 0,
        (1, "low"): 1,
        (1, "medium"): 2,
        (1, "high"): 3,
        (2, "high"): 4,
        (3, "high"): 5,
    }

    # Set Images
    image_idle_active_frames: list = ["images/idle-active-frame-1.bmp", "images/idle-active-frame-2.bmp"]
    image_idle_low_frames: list = ["images/idle-low-frame-1.bmp", "images/idle-low-frame-2.bmp"]
    image_idle_medium_frames: list = ["images/idle-medium-frame-1.bmp", "images/idle-medium-frame-2.bmp"]
    image_idle_high_frames: list = ["images/idle-high-frame-1.bmp", "images/idle-high-frame-2.bmp"]
    image_stim_active_frames: list = ["images/stim-active-frame-1.bmp", "images/stim-active-frame-2.bmp"]
    image_stim_low_frames: list = ["images/stim-low-frame-1.bmp", "images/stim-low-frame-2.bmp"]
    image_stim_medium_frames: list = ["images/stim-medium-frame-1.bmp", "images/stim-medium-frame-2.bmp"]
    image_stim_high_frames: list = ["images/stim-high-frame-1.bmp", "images/stim-high-frame-2.bmp"]
    image_cool_frames: list = ["images/cool-frame-1.bmp", "images/cool-frame-2.bmp"]
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
    image_idle_active_displays = [generate_image_display(image) for image in image_idle_active_frames]
    image_idle_low_displays = [generate_image_display(image) for image in image_idle_low_frames]
    image_idle_medium_displays = [generate_image_display(image) for image in image_idle_medium_frames]
    image_idle_high_displays = [generate_image_display(image) for image in image_idle_high_frames]
    image_orgasm_displays = [generate_image_display(image) for image in image_orgasm_frames]
    image_stim_active_displays = [generate_image_display(image) for image in image_stim_active_frames]
    image_stim_low_displays = [generate_image_display(image) for image in image_stim_low_frames]
    image_stim_medium_displays = [generate_image_display(image) for image in image_stim_medium_frames]
    image_stim_high_displays = [generate_image_display(image) for image in image_stim_high_frames]
    image_cool_displays = [generate_image_display(image) for image in image_cool_frames]
    image_displays_categories = {
        (1, "active"): image_idle_active_displays,
        (1, "low"): image_idle_low_displays,
        (1, "medium"): image_idle_medium_displays,
        (1, "high"): image_idle_high_displays,
        (2, "high"): image_orgasm_displays,
        (3, "high"): image_cool_displays,
    }
    image_displays_stim_categories = {
        "active": image_stim_active_displays,
        "low": image_stim_low_displays,
        "medium": image_stim_medium_displays,
        "high": image_stim_high_displays,
    }

    @classmethod
    async def display_images_and_text(cls):
        # Set Text
        txt_color: int = 0x030B00
        txt_font: str = terminalio.FONT
        txt_line_spacing: int = 0.8
        txt_scale: int = 1
        sroll_text = adafruit_display_text.label.Label(
            txt_font,
            color=txt_color,
            line_spacing=txt_line_spacing,
            scale=txt_scale,
            text="",
        )
        sroll_text.x = 14
        sroll_text.y = 56
        group = displayio.Group()
        group.append(sroll_text)
        DISPLAY.show(group)

        current_text_ptr = 999

        # use this to track stimulation frames
        stimulation_display_progress = 0
        normal_display_progress = 0
        normal_display_buffer = 10

        # TODO: replace this filler with a GLITCH IMAGE
        # group.append(GLITCH)
        group.append(cls.image_idle_high_displays[1])  # buffer for the first removal

        while True:
            if Session.state == 0:
                if len(group) > 1:
                    group.pop()
                    sroll_text.text = ""
                await asyncio.sleep(0.1)
                continue

            # Update text if needed
            if current_text_ptr != cls.text_categories_ptrs[(Session.state, Session.progress)]:
                current_text_ptr = cls.text_categories_ptrs[(Session.state, Session.progress)]
                sroll_text.text = cls.text_categories[(Session.state, Session.progress)]

            # update the text scroll position
            x = sroll_text.x - 2
            if x < -300:
                x = 14
            sroll_text.x = x

            # find the next frame to display
            if Session.stimulation:
                frame = cls.image_displays_stim_categories[Session.progress][stimulation_display_progress]
                if stimulation_display_progress == 1:
                    stimulation_display_progress = 0
                    Session.stimulation = False
                else:
                    stimulation_display_progress += 1
            elif Session.state == 2:  # ORGASM
                if normal_display_progress < 10:
                    frame_number = 0
                elif normal_display_progress < 20:
                    frame_number = 1
                elif normal_display_progress < 30:
                    frame_number = 2
                elif normal_display_progress < 40:
                    frame_number = 3
                elif normal_display_progress < 50:
                    frame_number = 4
                else:
                    frame_number = 5
                    if normal_display_progress > 60:
                        normal_display_progress = 0
                normal_display_progress += 1
                frame = cls.image_displays_categories[(Session.state, Session.progress)][frame_number]
            else:
                if normal_display_progress > 0:
                    frame_number = 0
                    normal_display_progress += 1
                    if normal_display_progress > normal_display_buffer:
                        normal_display_progress = -1
                else:
                    frame_number = 1
                    normal_display_progress -= 1
                    if normal_display_progress < -normal_display_buffer:
                        normal_display_progress = 1
                frame = cls.image_displays_categories[(Session.state, Session.progress)][frame_number]

            # Now, display the new frame
            if len(group) > 1:
                group.pop()
            group.append(frame)
            await asyncio.sleep(0.01)


async def main():
    interrupt_task_l1 = asyncio.create_task(stimulator(button_l_1))
    interrupt_task_l2 = asyncio.create_task(stimulator(button_l_2))
    interrupt_task_l3 = asyncio.create_task(stimulator(button_l_3))
    interrupt_task_r1 = asyncio.create_task(stimulator(button_r_1))
    interrupt_task_r2 = asyncio.create_task(stimulator(button_r_2))
    interrupt_task_r3 = asyncio.create_task(stimulator(button_r_3))
    display_task = asyncio.create_task(Display.display_images_and_text())
    looper_task = asyncio.create_task(orchestrator())
    beeper_task = asyncio.create_task(beeper())
    await asyncio.gather(
        beeper_task,
        looper_task,
        display_task,
        interrupt_task_l1,
        interrupt_task_l2,
        interrupt_task_l3,
        interrupt_task_r1,
        interrupt_task_r2,
        interrupt_task_r3,
    )


asyncio.get_event_loop().run_until_complete(main())
