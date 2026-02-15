import keyboard
import time


def backspace_and_write(s: str):
    for _ in s:
        keyboard.press_and_release('backspace')
    keyboard.write(s)


# to_write = "THIS_IS_A_VERY_LONG_STRING_WITH_UNDERSCORES_AND_CAPITAL_LETTERS_WHY_TO_TEST_OFCOURSE_I_WONDER_IF_IT_WILL_WORK_OUT_OKAY_OR_IF_IT_WILL_FAIL_HORRIBLY"
# to_write = "this is a very long string with no underscords or capitial letters why to test ofcourse i wonder if it will work out okay or if it will fail horribly"
# to_write = "short"
to_write = "slightly longer"


def main():
    time.sleep(5)
    keyboard.write(to_write)
    while True:
        backspace_and_write(to_write)
        time.sleep(.1)


if __name__ == "__main__":
    main()
