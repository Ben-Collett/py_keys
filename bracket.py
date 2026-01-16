import keyboard
import time


def hook(event):
    print(event.name)


def main():
    keyboard.hook(hook)
    time.sleep(2)
    keyboard.write("[")

    keyboard.wait()


if __name__ == "__main__":
    main()
