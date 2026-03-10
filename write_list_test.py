import keyboard
import time
if __name__ == "__main__":
    # expented output => "h "
    time.sleep(3)
    # keyboard.write("hello_there")

    keyboard.write_list(["h", "i", " ", "left", "backspace", "right"])
