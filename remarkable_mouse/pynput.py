import logging
import struct
from screeninfo import get_monitors

# from .codes import EV_SYN, EV_ABS, ABS_X, ABS_Y, BTN_TOUCH
from .codes import codes
from .common import get_monitor, log_event

logging.basicConfig(format='%(message)s')
log = logging.getLogger('remouse')

# wacom digitizer dimensions
# touchscreen dimensions
# finger_width = 767
# finger_height = 1023


def read_tablet(rm, *, orientation, monitor_num, region, threshold, mode, touch):
    """Loop forever and map evdev events to mouse

    Args:
        rm (reMarkable): tablet settings and input streams
        orientation (str): tablet orientation
        monitor_num (int): monitor number to map to
        region (boolean): whether to selection mapping region with region tool
        threshold (int): pressure threshold
        mode (str): mapping mode
    """

    from pynput.mouse import Button, Controller

    mouse = Controller()

    monitor, _ = get_monitor(region, monitor_num, orientation)
    log.debug('Chose monitor: {}'.format(monitor))

    x = y = 0

    stream = rm.pen
    last_touch_state = False
    previous = 0
    while True:
        try:
            # read evdev events from file stream
            data = stream.read(struct.calcsize(rm.e_format))
        except TimeoutError:
            continue

        # parse evdev events
        e_time, e_millis, e_type, e_code, e_value = struct.unpack(
            rm.e_format, data)

        if log.level == logging.DEBUG:
            log_event(e_time, e_millis, e_type, e_code, e_value)

        try:

            if codes[e_type][e_code] == 'BTN_STYLUS':
                if touch == "button":
                    if e_value == 1:
                        mouse.press(Button.left)
                    else:
                        mouse.release(Button.left)
                if touch=="normal":
                    if e_value == 1:
                        mouse.press(Button.right)
                    else:
                        mouse.release(Button.right)
            # handle x direction
            if codes[e_type][e_code] == 'ABS_X':
                x = e_value

            # handle y direction
            if codes[e_type][e_code] == 'ABS_Y':
                y = e_value

            # handle draw
             # Tracks the previous touch state

# Then modify your BTN_TOUCH handling:
            if codes[e_type][e_code] == 'BTN_TOUCH':
                if touch == "click":

                    current_touch = (e_value == 1)

                    # On release (transition from touching to not touching)
                    if not current_touch and last_touch_state:
                        # Click action - press and release quickly
                        mouse.press(Button.left)
                        mouse.release(Button.left)

                    last_touch_state = current_touch
                elif touch == "normal":
                    if e_value == 1:
                        mouse.press(Button.left)
                    else:
                        mouse.release(Button.left)

            if codes[e_type][e_code] == 'SYN_REPORT':
                mapped_x, mapped_y = rm.remap(
                    x, y,
                    rm.pen_x.max, rm.pen_y.max,
                    monitor.width, monitor.height,
                    mode, orientation,
                )
                mouse.move(
                    monitor.x + mapped_x - mouse.position[0],
                    monitor.y + mapped_y - mouse.position[1]
                )
        except KeyError as e:
            log.debug(f"Invalid evdev event: type:{e_type} code:{e_code}")
