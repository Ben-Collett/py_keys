import keyboard.mouse as mouse


def on_event(event):
    if isinstance(event, mouse.ButtonEvent):
        print(f"Button {event.event_type}: {event.button} at {event.time}")
    elif isinstance(event, mouse.MoveEvent):
        print(f"Move to ({event.x}, {event.y}) at {event.time}")
    elif isinstance(event, mouse.WheelEvent):
        print(f"Wheel delta={event.delta} at {event.time}")


if __name__ == "__main__":
    mouse.hook(on_event)
    print("Listening for mouse events. Press Ctrl+C to stop.")
    try:
        from time import sleep
        while True:
            sleep(1)
    except KeyboardInterrupt:
        mouse.unhook(on_event)
        print("\nStopped.")
