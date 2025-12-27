
from evdev import InputDevice, UInput, ecodes
from threading import Thread
from time import sleep

# ======================
# CONFIG
# ======================

EXPECTED = 100
KEY = ecodes.KEY_BACKSPACE

# Pick a real keyboard device:
# run: ls /dev/input/by-id/
DEVICE_PATH = "/dev/input/event14"

# ======================
# STATE
# ======================

expected = EXPECTED
running = True

# ======================
# EVENT READER
# ======================


def read_events(dev: InputDevice):
    global expected, running

    for event in dev.read_loop():
        if not running:
            break

        if event.type == ecodes.EV_KEY and event.code == KEY:
            if event.value == 1:  # KEY_DOWN
                print("backspace")
                expected -= 1
                print(expected)

# ======================
# MAIN
# ======================


def main():
    global running

    dev = InputDevice(DEVICE_PATH)
    print(f"Listening on: {dev.path} ({dev.name})")

    # uinput virtual keyboard
    ui = UInput({ecodes.EV_KEY: [KEY]}, name="evdev-test")

    t = Thread(target=read_events, args=(dev,), daemon=True)
    t.start()

    # give listener time to start
    sleep(0.1)

    for _ in range(EXPECTED):
        ui.write(ecodes.EV_KEY, KEY, 1)  # press
        ui.write(ecodes.EV_KEY, KEY, 0)  # release
        ui.syn()
        sleep(0.001)  # stable timing

    sleep(0.5)
    running = False
    ui.close()


if __name__ == "__main__":
    main()
