import asyncio
import board
import keypad
import displayio
import framebufferio
import rgbmatrix
import time
from divide_and_display import Display


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
    categories = {
        (0, 10): "active",
        (10, 33): "low",
        (33, 66): "medium",
        (66, 100): "high"
    }
    for interval, category in categories.items():
        if interval[0] <= progress_percentage < interval[1]:
            return category
    return "high"


class Session:
    stimulation_log: list = []
    strokes_goal: int = 3
    velocity_goal: int = 3
    stimulation_evaluation_pointer: int = 0
    stroke_count: int = 0
    session_started_at: timestamp
    session_succeeded_at: timestamp
    state: int = 0  # 0 - idel; 1 - operating; 2 - success
    progress: str = "active"

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
            elif cls.stimulation_log[i].button_number == ordered_button_numbers[j-1]:
                pass
            else:
                stroke_starts_from = i
            i += 1
        if j == 3 and cls.stimulation_log[i-1].received_at - cls.stimulation_log[stroke_starts_from].received_at < cls.velocity_goal:
            print(f"Left strokes: {Session.stroke_count}; state: {Session.state}")
            cls.stroke_count += 1
            cls.stimulation_evaluation_pointer = i
            cls.progress = categorize_session_progress(cls.stroke_count / cls.strokes_goal * 100)
            if cls.stroke_count < cls.strokes_goal:
                await Display.display_images_and_text(state=cls.state, progress=cls.progress, stimulation=True)


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
        if Session.state == 0:  # idle
            if Session.stimulation_log == []:
                pass
            elif time.time() - Session.stimulation_log[-1].received_at < 1:
                print(f"current time: {time.time()}")
                print(f"button time: {Session.stimulation_log[-1].received_at}")
                Session.state = 1
                Session.progress = "active"
                Session.stimulation_log = [Session.stimulation_log[-1]]
                Session.stroke_count = 0
                Session.stimulation_evaluation_pointer = 0
        elif Session.state == 1:  # active
            if Session.stroke_count >= Session.strokes_goal:
                Session.session_succeeded_at = time.time()
                Session.state = 2
            elif time.time() - Session.stimulation_log[-1].received_at > 30:
                Session.state = 0
        elif Session.state == 2:  # success
            if time.time() - Session.session_succeeded_at < 5:
                # await Display.display_images_and_text(display_type="alternation")
                pass
            elif time.time() - Session.session_succeeded_at < 30:
                # display cool-down images:
                pass
            else:
                Session.state = 0

        await Session.detect_upto_one_stroke()
        print(f"Left strokes: {Session.stroke_count}; state: {Session.state}")
        await Display.display_images_and_text(state=Session.state, progress=Session.progress)
        await asyncio.sleep(0.5)


async def main():
    interrupt_task_l1 = asyncio.create_task(stimulator(button_l_1))
    interrupt_task_l2 = asyncio.create_task(stimulator(button_l_2))
    interrupt_task_l3 = asyncio.create_task(stimulator(button_l_3))
    interrupt_task_r1 = asyncio.create_task(stimulator(button_r_1))
    interrupt_task_r2 = asyncio.create_task(stimulator(button_r_2))
    interrupt_task_r3 = asyncio.create_task(stimulator(button_r_3))
    looper_task = asyncio.create_task(orchestrator())
    await asyncio.gather(looper_task, interrupt_task_l1, interrupt_task_l2, interrupt_task_l3, interrupt_task_r1, interrupt_task_r2, interrupt_task_r3)

asyncio.get_event_loop().run_until_complete(main())
