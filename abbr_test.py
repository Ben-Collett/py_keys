from buffer import RingBuffer
import keyboard


def main():
    keyboard.init(
        linux_collision_safety_mode=keyboard.LinuxCollisionSafetyModes.PATIENT,
        windows_synetic_mode=keyboard.WindowsSyntheticModes.REAL,
        device_name="abbr test keyboard"
    )
    # space_queue = Queue()

    b = RingBuffer(capacity=100)

    def add_key(event: keyboard.KeyboardEvent):
        print(event.device_name)

        # if event.event_type == keyboard.KEY_DOWN:
        #     print(event.name, event.modifiers)

        if event.event_type == keyboard.KEY_UP:

            print(event.name, event.event_type)
            # print("a", event.name)
            if event.name == "space":
                # print("spaced")
                prev = b.get_prev_word()

                # print("prev word", prev)
                if prev == "df":
                    for i in range(3):
                        keyboard.press_and_release("backspace")

                    # to_write = "hEelLlo ;.?#@"
                    # to_write = r'd'
                    # to_write = "that "
                    to_write = r"d!i[F!fere?nt [{}] \ "
                    # to_write = "d!iF!fere?nt "
                    keyboard.write(to_write)
                    # for ch in to_write:
                    #     keyboard.press_and_release(ch)
                    #     time.sleep(.01)
            return

        if event.name == "backspace":
            b.backspace()
            # print("back")
        elif event.name == "space":
            b.add(" ")
        elif event.name == "windows":
            b.clear()
        elif len(event.name) == 1:
            b.add(event.name)
        # print(b)

    keyboard.hook(add_key)
    keyboard.wait()
    # keyboard.wait(hotkey="alt gr")


if __name__ == "__main__":
    main()
