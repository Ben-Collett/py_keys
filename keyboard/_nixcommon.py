# -*- coding: utf-8 -*-
import re
import struct
from io import BufferedWriter
import os
import fcntl
import signal
import atexit
from ._nixlibudev import set_up_libudev, create_udev_monitor, monitor_on_add
from time import time as now
from time import sleep
from threading import Thread
from glob import glob
from multiprocessing import Queue, Process

# EVIOCGRAB ioctl: grab/release exclusive access to evdev device
# Argument: 1 to grab, 0 to release
EVIOCGRAB = 0x40044590

# l = long, H = unsigned short,I = unsigned int
event_bin_format = "llHHI"


# Taken from include/linux/input.h
# https://www.kernel.org/doc/Documentation/input/event-codes.txt

# sync event
EV_SYN = 0x00
# key event
EV_KEY = 0x01
# mouse relative movement, like 5 left
EV_REL = 0x02
# abs position like touching a screen
EV_ABS = 0x03
# miscellanesus event
EV_MSC = 0x04


try:
    _lib_udev = set_up_libudev()
except BaseException:
    _lib_udev = None


def make_uinput(name: str):
    if not os.path.exists("/dev/uinput"):
        raise IOError("No uinput module found.")

    from ._nixutils import make_keyboard

    # Requires uinput driver, but it's usually available.
    uinput = open("/dev/uinput", "wb")

    make_keyboard(uinput, name)

    return uinput


class EventDevice(object):
    def __init__(self, path):
        self.path = path
        self._input_file = None
        self._output_file = None
        self._sysfs_name = None

    @property
    def sysfs_name(self):
        if self._sysfs_name is None:
            match = re.search(r"event(\d+)", self.path)
            if match:
                event_num = match.group(1)
                sysfs_path = f"/sys/class/input/event{event_num}/device/name"
                try:
                    with open(sysfs_path, "r") as f:
                        self._sysfs_name = f.read().strip()
                except (IOError, OSError):
                    self._sysfs_name = None
            else:
                self._sysfs_name = None
        return self._sysfs_name

    @property
    def input_file(self):
        if self._input_file is None:
            try:
                self._input_file: BufferedWriter = open(self.path, "rb")
            except IOError as e:
                if e.strerror == "Permission denied":
                    print(
                        f"# ERROR: Failed to read device '{
                            self.path
                        }'. You must be in the 'input' group to access global events. Use 'sudo usermod -a -G input USERNAME' to add user to the required group. Or just run the program with root privlages"
                    )
                    exit()

        return self._input_file

    @property
    def output_file(self):
        if self._output_file is None:
            self._output_file = open(self.path, "wb")
            atexit.register(self._output_file.close)
        return self._output_file

    def read_event(self):
        data = self.input_file.read(struct.calcsize(event_bin_format))
        seconds, microseconds, type, code, value = struct.unpack(event_bin_format, data)

        return (
            seconds + microseconds / 1e6,
            type,
            code,
            value,
            self.path,
            self.sysfs_name,
        )

    def write_event(self, type, code, value):
        integer, fraction = divmod(now(), 1)
        seconds = int(integer)
        microseconds = int(fraction * 1e6)
        data_event = struct.pack(
            event_bin_format, seconds, microseconds, type, code, value
        )

        # Send a sync event to ensure other programs update.
        sync_event = struct.pack(event_bin_format, seconds, microseconds, EV_SYN, 0, 0)

        self.output_file.write(data_event + sync_event)
        self.output_file.flush()

    def grab(self):
        """Grab exclusive access to this device. Other processes won't receive events."""
        fd = self.input_file.fileno()
        fcntl.ioctl(fd, EVIOCGRAB, 1)

    def ungrab(self):
        """Release exclusive access to this device."""
        fd = self.input_file.fileno()
        fcntl.ioctl(fd, EVIOCGRAB, 0)


def device_reader_worker(device_paths, event_queue, command_queue, virtual_name):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    devices = [EventDevice(p) for p in device_paths]

    # Track grabbed devices - use mutable containers for thread sharing
    grabbed_devices = set()
    is_grabbed = [False]  # List as mutable container

    def is_virtual_device(device):
        """Check if this is the virtual keyboard created by the program."""
        return device.sysfs_name == virtual_name

    def grab_device(device):
        """Grab a device if it's not the virtual keyboard."""
        if is_virtual_device(device):
            return False
        try:
            device.grab()
            grabbed_devices.add(device.path)
            return True
        except OSError:
            return False

    def ungrab_device(device):
        """Release a grabbed device."""
        if device.path not in grabbed_devices:
            return
        try:
            device.ungrab()
        except OSError:
            pass
        grabbed_devices.discard(device.path)

    def read_loop(device):
        while True:
            try:
                event_queue.put(device.read_event(), block=True)
            except OSError:
                break

    for d in devices:
        Thread(target=read_loop, args=(d,), daemon=True).start()

    def add_device(path):
        device = EventDevice(path)
        devices.append(device)
        Thread(target=read_loop, args=(device,), daemon=True).start()
        if is_grabbed[0]:
            grab_device(device)

    def grab_all_connected():
        for device in devices:
            if device.path not in grabbed_devices:
                grab_device(device)

    def ungrab_all_connected():
        for path in list(grabbed_devices):
            for device in devices:
                if device.path == path:
                    ungrab_device(device)
                    break
    def command_listener():
        """Listen for grab/ungrab commands from main process."""
        while True:
            try:
                cmd = command_queue.get(block=True)
                if cmd == 'grab':
                    if not is_grabbed[0]:
                        is_grabbed[0] = True
                        grab_all_connected()
                elif cmd == 'ungrab':
                    if is_grabbed[0]:
                        is_grabbed[0] = False
                        ungrab_all_connected()
            except OSError:
                break

    # Start command listener thread
    Thread(target=command_listener, daemon=True).start()

    if _lib_udev:
        try:
            udev, mon, fd = create_udev_monitor(_lib_udev)
            monitor_on_add(_lib_udev, mon, add_device)
        except BaseException:
            pass

    # only should be reached if monitor fails
    while True:
        sleep(1e6)


class AggregatedEventDevice:
    def __init__(self, devices, output=None, virtual_name=None):
        self.event_queue = Queue()
        self.command_queue = Queue()  # For sending grab/ungrab commands

        self.output = output  # stays in parent only
        self.grabbed = False
        paths = [d.path for d in devices]

        self.process = Process(
            target=device_reader_worker,
            args=(paths, self.event_queue, self.command_queue, virtual_name),
            daemon=True,
        )
        self.process.start()

    def read_event(self):
        # Blocks until an event is available
        return self.event_queue.get()

    def write_event(self, type, code, value):
        self.output.write_event(type, code, value)

    def grab(self):
        """Grab exclusive access to all keyboards except the virtual one."""
        if not self.grabbed:
            self.grabbed = True
            self.command_queue.put('grab')

    def ungrab(self):
        """Release exclusive access to keyboards."""
        if self.grabbed:
            self.grabbed = False
            self.command_queue.put('ungrab')


device_pattern = r"""N: Name="([^"]+?)".+?H: Handlers=([^\n]+)"""


def list_devices_from_proc(type_name):
    try:
        with open("/proc/bus/input/devices") as f:
            description = f.read()
    except FileNotFoundError:
        return

    for name, handlers in re.findall(device_pattern, description, re.DOTALL):
        path = "/dev/input/event" + re.search(r"event(\d+)", handlers).group(1)
        if type_name in handlers:
            yield EventDevice(path)


def list_devices_from_by_id(name_suffix, by_id=True):
    for path in glob(
        "/dev/input/{}/*-event-{}".format("by-id" if by_id else "by-path", name_suffix)
    ):
        yield EventDevice(path)


def aggregate_devices(type_name, name: str):
    # Some systems have multiple keyboards with different range of allowed keys
    # on each one, like a notebook with a "keyboard" device exclusive for the
    # power button. Instead of figuring out which keyboard allows which key to
    # send events, we create a fake device and send all events through there.
    try:
        uinput = make_uinput(name)
        fake_device = EventDevice("uinput Fake Device")
        fake_device._input_file = uinput
        fake_device._output_file = uinput
    except IOError:
        import warnings

        warnings.warn(
            "Failed to create a device file using `uinput` module. Sending of events may be limited or unavailable depending on plugged-in devices.",
            stacklevel=2,
        )
        fake_device = None

    # We don't aggregate devices from different sources to avoid
    # duplicates.

    devices_from_proc = list(list_devices_from_proc(type_name))
    if devices_from_proc:
        return AggregatedEventDevice(devices_from_proc, output=fake_device, virtual_name=name)

    # breaks on mouse for virtualbox
    # was getting /dev/input/by-id/usb-VirtualBox_USB_Tablet-event-mouse
    devices_from_by_id = list(list_devices_from_by_id(type_name)) or list(
        list_devices_from_by_id(type_name, by_id=False)
    )
    if devices_from_by_id:
        return AggregatedEventDevice(devices_from_by_id, output=fake_device, virtual_name=name)

    # If no keyboards were found we can only use the fake device to send keys.
    assert fake_device
    return fake_device
