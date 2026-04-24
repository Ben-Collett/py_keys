import keyboard
import time

def hook(event:keyboard.KeyboardEvent):
    if event.event_type == keyboard.KEY_DOWN and event.name == "a":
        print("dog")
    elif event.name != "a":
        keyboard.propagate(event)

if __name__ == "__main__":
    keyboard.init(auto_grab=True)
    keyboard.hook(hook)
    time.sleep(3)
    keyboard.ungrab()
    time.sleep(3)
    
