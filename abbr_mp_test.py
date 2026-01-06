from buffer import RingBuffer
import keyboard
import multiprocessing
import threading

keyboard.patient_collision_safe_mode()
b = RingBuffer(capacity=100)
event_queue = multiprocessing.Queue()


def process_event():
    while True:
        print("reading event")
        event = event_queue.get()
        print(event)
        if event.event_type == keyboard.KEY_UP:
            if event.name == "space":
                prev = b.get_prev_word()
                if prev == "df":
                    for i in range(3):
                        keyboard.press_and_release("backspace")
                    to_write = "diFferent "
                    keyboard.write(to_write)
            continue

        if event.name == "backspace":
            b.backspace()
            print("back")
        elif event.name == "space":
            b.add(" ")
        elif event.name == "windows":
            b.clear()
        elif len(event.name) == 1:
            b.add(event.name)


def add_to_queue(event):
    event_queue.put(event)


# multiprocessing.Process(target=process_event).start()
threading.Thread(target=process_event).start()
keyboard.hook(add_to_queue)
keyboard.wait(hotkey="alt")
