import keyboard
from time import sleep
keyboard.init(
    linux_collision_safety_mode=keyboard.LinuxCollisionSafetyModes.PATIENT)

sleep(2)


def nop(event):
    print(event.name)


keyboard.hook(nop)
keyboard.press("shift")
keyboard.write("heLlo theRe")
keyboard.press("a")
keyboard.release("a")
keyboard.release("shift")

keyboard.wait()
