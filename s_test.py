import keyboard
from time import sleep
expected = 1000
# out_str = "backspace, "*(expected-1) + "backspace"


def dec_print(event: keyboard.KeyboardEvent):
    global expected

    # for i in range(1_000_0000):
    #     pass

    # print(event.name)
    if event.name == "backspace" and event.event_type == keyboard.KEY_DOWN:
        expected -= 1
        print(expected)


def main():
    keyboard.hook(dec_print)
    # keyboard.press_and_release(out_str)
    for i in range(expected):
        keyboard.press_and_release("backspace")
        # sleep(.000000000000001)

    keyboard.wait()


if __name__ == "__main__":
    main()
