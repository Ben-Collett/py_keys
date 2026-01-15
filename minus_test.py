import keyboard
print(hex(ord("-")))


def pr(event):
    print(event.name, hex(ord(event.name)))


keyboard.hook(pr)
keyboard.wait()
