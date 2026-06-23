# -*- coding: utf-8 -*-
import os
import struct
from subprocess import check_output
import re
from ._nixcommon import EV_KEY, EV_REL, EV_MSC, EV_SYN, EV_ABS, aggregate_devices
from ._mouse_event import ButtonEvent, WheelEvent, MoveEvent, LEFT, RIGHT, MIDDLE, X, X2, UP, DOWN

import ctypes
import ctypes.util
from ctypes import c_uint32, c_uint, c_int, byref

display = None
window = None
x11 = None
confirmed_no_x11 = False


def build_display():
    global display, window, x11, confirmed_no_x11
    if display and window and x11:
        return
    if 'WAYLAND_DISPLAY' in os.environ:
        confirmed_no_x11 = True
        return
    try:
        x11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library('X11'))
        x11.XInitThreads()
        x11.XOpenDisplay.restype = ctypes.c_void_p
        stderr_fd = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        try:
            display = x11.XOpenDisplay(None)
        finally:
            os.dup2(stderr_fd, 2)
            os.close(devnull)
            os.close(stderr_fd)
        if not display:
            raise OSError(
                "XOpenDisplay returned NULL (no X11 display available)")
        window = x11.XDefaultRootWindow(display)
    except BaseException:
        confirmed_no_x11 = True


def get_position():
    build_display()
    if confirmed_no_x11:
        return -1, -1
    root_id, child_id = c_uint32(), c_uint32()
    root_x, root_y, win_x, win_y = c_int(), c_int(), c_int(), c_int()
    mask = c_uint()
    ret = x11.XQueryPointer(display, c_uint32(window), byref(root_id), byref(child_id),
                            byref(root_x), byref(root_y),
                            byref(win_x), byref(win_y), byref(mask))
    return root_x.value, root_y.value


def move_to(x, y):
    build_display()
    if confirmed_no_x11:
        return
    x11.XWarpPointer(display, None, window, 0, 0, 0, 0, x, y)
    x11.XFlush(display)


REL_X = 0x00
REL_Y = 0x01
REL_Z = 0x02
REL_HWHEEL = 0x06
REL_WHEEL = 0x08

ABS_X = 0x00
ABS_Y = 0x01

BTN_MOUSE = 0x110
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112
BTN_SIDE = 0x113
BTN_EXTRA = 0x114

button_by_code = {
    BTN_LEFT: LEFT,
    BTN_RIGHT: RIGHT,
    BTN_MIDDLE: MIDDLE,
    BTN_SIDE: X,
    BTN_EXTRA: X2,
}
code_by_button = {button: code for code, button in button_by_code.items()}

device = None


def build_device():
    global device
    if device:
        return
    device = aggregate_devices('mouse', "py_keys_mouse")


init = build_device


def listen(queue):
    build_device()

    while True:
        time, type, code, value, device_id, device_name = device.read_event()
        if type == EV_SYN or type == EV_MSC:
            continue

        event = None
        arg = None

        if type == EV_KEY:
            event = ButtonEvent(DOWN if value else UP,
                                button_by_code.get(code, '?'), time)
        elif type == EV_REL:
            value, = struct.unpack('i', struct.pack('I', value))

            if code == REL_WHEEL:
                event = WheelEvent(value, time)
            elif code in (REL_X, REL_Y):
                x, y = get_position()
                event = MoveEvent(x, y, time)

        if event is None:
            # Unknown event type.
            continue

        queue.put(event)


def press(button=LEFT):
    build_device()
    device.write_event(EV_KEY, code_by_button[button], 0x01)


def release(button=LEFT):
    build_device()
    device.write_event(EV_KEY, code_by_button[button], 0x00)


def move_relative(x, y):
    build_device()
    # Note relative events are not in terms of pixels, but millimeters.
    if x < 0:
        x += 2**32
    if y < 0:
        y += 2**32
    device.write_event(EV_REL, REL_X, x)
    device.write_event(EV_REL, REL_Y, y)


def wheel(delta=1):
    build_device()
    if delta < 0:
        delta += 2**32
    device.write_event(EV_REL, REL_WHEEL, delta)


if __name__ == '__main__':
    # listen(print)
    move_to(100, 200)
