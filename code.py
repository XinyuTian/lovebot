import asyncio
import board
import keypad
import time


class Stimulation:
    def __init__(self, button_name, received_at):
        self.button_name = button_name
        self.received_at = received_at


class Button:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin


button_stroke_names = ["L1_blue", "L2_green", "L3_red"]
button_b = Button(button_stroke_names[0], board.GP15)
button_g = Button(button_stroke_names[1], board.GP28)
button_r = Button(button_stroke_names[2], board.GP27)


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

    @classmethod
    def detect_upto_one_left_stroke(cls):
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

    def session_state(self):
        pass


class Orchestrator:
    status: str # enum active/inactive
    happiness_count: int=0

    def get_session_state(session):
        pass


async def catch_pin_transitions(button):
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

async def looper():
    while(True):
        Session.detect_upto_one_left_stroke()
        print(f"Left strokes: {Session.left_stroke_count}")
        await asyncio.sleep(0.5)

async def main():
    interrupt_task_b = asyncio.create_task(catch_pin_transitions(button_b))
    interrupt_task_g = asyncio.create_task(catch_pin_transitions(button_g))
    interrupt_task_r = asyncio.create_task(catch_pin_transitions(button_r))
    looper_task = asyncio.create_task(looper())
    await asyncio.gather(interrupt_task_b, interrupt_task_g, interrupt_task_r, looper_task)

asyncio.get_event_loop().run_until_complete(main())
