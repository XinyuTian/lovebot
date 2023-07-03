import asyncio
import board
import keypad
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


class Stimulation:
    def __init__(self, button_name, received_at):
        self.button_name = button_name
        self.received_at = received_at


class Button:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin


button_stroke_names = ["L1_blue", "L2_green", "L3_red"]
button_b = Button(button_stroke_names[0], board.GP28)
button_g = Button(button_stroke_names[1], board.GP27)
button_r = Button(button_stroke_names[2], board.GP26)


async def display_one_frame(image):
    bitmap = displayio.OnDiskBitmap(open(image, 'rb'))
    group = displayio.Group()
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
    time.sleep(0.5)
    DISPLAY.refresh()


class Session:
    stimulation_left_log: list = []
    stimulation_right_log: list = []
    strokes_goal: int = 3
    velocity_goal: int = 2
    left_pointer: int = 0
    right_pointer: int = 0
    left_stroke_count: int = 0
    right_stroke_count: int = 0
    session_started_at: timestamp
    session_succeeded_at: timestamp
    state: int = 0 # 0 - idel; 1 - operating; 2 - success

    @classmethod
    async def detect_upto_one_left_stroke(cls):
        i = cls.left_pointer
        j = 0 # button_stroke_name_pointer
        stroke_starts_from = -1
        while i < len(cls.stimulation_left_log) and j <= 2:
            if cls.stimulation_left_log[i].button_name == button_stroke_names[0]:
                stroke_starts_from = i
                i += 1
                j = 1
                continue
            if cls.stimulation_left_log[i].button_name == button_stroke_names[j]:
                j += 1
            elif cls.stimulation_left_log[i].button_name == button_stroke_names[j-1]:
                pass
            else:
                stroke_starts_from = -1
            i += 1
        if j == 3 and cls.stimulation_left_log[i-1].received_at - cls.stimulation_left_log[stroke_starts_from].received_at < cls.velocity_goal:
            cls.left_stroke_count += 1
            cls.left_pointer = i
            if cls.left_stroke_count < cls.strokes_goal:
                await display_one_frame(image='rainbow.bmp')


async def stimulator(button):
    """Print a message when pin goes low and when it goes high."""
    with keypad.Keys((button.pin,), value_when_pressed=False) as keys:
        while True:
            event = keys.events.get()
            if event:
                if event.pressed:
                    stimulation = Stimulation(button.name, time.time())
                    Session.stimulation_left_log.append(stimulation)
                    print(stimulation.button_name, stimulation.received_at, len(Session.stimulation_left_log))
            await asyncio.sleep(0.1)


async def orchestrator():
    while True:
        if Session.state == 0: # idle
            if Session.stimulation_left_log == []:
                pass
            elif time.time() - Session.stimulation_left_log[-1].received_at < 1: # randomize session goal
                print(f"current time: {time.time()}")
                print(f"button time: {Session.stimulation_left_log[-1].received_at}")
                Session.state = 1
                Session.stimulation_left_log = [Session.stimulation_left_log[-1]]
                Session.left_stroke_count = 0
                Session.left_pointer = 0
        elif Session.state == 1: # active
            if Session.left_stroke_count >= Session.strokes_goal:
                Session.session_succeeded_at = time.time()
                Session.state = 2
            elif time.time() - Session.stimulation_left_log[-1].received_at > 30:
                Session.state = 0
        elif Session.state == 2: # success
            if time.time() - Session.session_succeeded_at < 5:
            #   display success images
                pass
            elif time.time() - Session.session_succeeded_at < 30:
            #   display cool-down images:
                pass
            else:
                Session.state = 0

        await Session.detect_upto_one_left_stroke()
        print(f"Left strokes: {Session.left_stroke_count}; state: {Session.state}")
        await display_one_frame(image='frame_1.bmp')
        await asyncio.sleep(0.5)


async def main():
    interrupt_task_b = asyncio.create_task(stimulator(button_b))
    interrupt_task_g = asyncio.create_task(stimulator(button_g))
    interrupt_task_r = asyncio.create_task(stimulator(button_r))
    looper_task = asyncio.create_task(orchestrator())
    await asyncio.gather(interrupt_task_b, interrupt_task_g, interrupt_task_r, looper_task)

asyncio.get_event_loop().run_until_complete(main())
