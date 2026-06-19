"""Move the Windows cursor after one idle minute during configured work periods.

No clicks are sent. Press Ctrl+C in the terminal to stop the script.
"""

from __future__ import annotations

import ctypes
import math
import random
import sys
import time as sleep_clock
from ctypes import wintypes
from datetime import datetime, time


IDLE_SECONDS = 60
POLL_SECONDS = 0.5
LOCK_POLL_SECONDS = 1.0
USER_MOVE_TOLERANCE_PIXELS = 4
DESKTOP_SWITCHDESKTOP = 0x0100

# Active windows are local machine time. End times are exclusive.
ACTIVE_WINDOWS = (
    (time(8, 0), time(12, 0)),
    (time(13, 12), time(18, 0)),
)


if sys.platform != "win32":
    raise SystemExit("This script uses the Windows cursor API and must run on Windows.")


user32 = ctypes.windll.user32


class Point(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


user32.GetCursorPos.argtypes = [ctypes.POINTER(Point)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.OpenDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.OpenDesktopW.restype = wintypes.HANDLE
user32.SwitchDesktop.argtypes = [wintypes.HANDLE]
user32.SwitchDesktop.restype = wintypes.BOOL
user32.CloseDesktop.argtypes = [wintypes.HANDLE]
user32.CloseDesktop.restype = wintypes.BOOL

try:
    user32.SetProcessDPIAware()
except AttributeError:
    pass


def active_now() -> bool:
    current = datetime.now().time()
    return any(start <= current < end for start, end in ACTIVE_WINDOWS)


def log_action(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def default_desktop_available() -> bool:
    desktop = user32.OpenDesktopW("Default", 0, False, DESKTOP_SWITCHDESKTOP)
    if not desktop:
        return False

    try:
        return bool(user32.SwitchDesktop(desktop))
    finally:
        user32.CloseDesktop(desktop)


def pause_for_lock_screen() -> float:
    if default_desktop_available():
        return 0.0

    log_action("Windows lock screen detected. Pausing until unlock.")
    paused_at = sleep_clock.monotonic()

    while not default_desktop_available():
        sleep_clock.sleep(LOCK_POLL_SECONDS)

    paused_for = sleep_clock.monotonic() - paused_at
    log_action("Windows unlocked. Resuming.")
    return paused_for


def cursor_position() -> tuple[int, int]:
    while True:
        pause_for_lock_screen()
        point = Point()
        if user32.GetCursorPos(ctypes.byref(point)):
            return point.x, point.y
        if default_desktop_available():
            raise ctypes.WinError()


def set_cursor_position(position: tuple[int, int]) -> None:
    x, y = position
    while True:
        pause_for_lock_screen()
        if user32.SetCursorPos(int(x), int(y)):
            return
        if default_desktop_available():
            raise ctypes.WinError()


def virtual_screen_bounds() -> tuple[int, int, int, int]:
    left = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
    top = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
    width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
    height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN

    if width <= 0 or height <= 0:
        left = 0
        top = 0
        width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN

    return left, top, left + width - 1, top + height - 1


def clamp(value: float, low: int, high: int) -> int:
    return int(min(max(round(value), low), high))


def distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def pick_target(origin: tuple[int, int], bounds: tuple[int, int, int, int]) -> tuple[int, int]:
    left, top, right, bottom = bounds
    margin = 24
    safe_left = min(left + margin, right)
    safe_top = min(top + margin, bottom)
    safe_right = max(left, right - margin)
    safe_bottom = max(top, bottom - margin)

    for _ in range(10):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(55, 210)
        target = (
            clamp(origin[0] + math.cos(angle) * radius, safe_left, safe_right),
            clamp(origin[1] + math.sin(angle) * radius, safe_top, safe_bottom),
        )
        if distance(origin, target) >= 35:
            return target

    return (
        clamp((safe_left + safe_right) / 2, safe_left, safe_right),
        clamp((safe_top + safe_bottom) / 2, safe_top, safe_bottom),
    )


def smoothstep(value: float) -> float:
    return value * value * (3 - 2 * value)


def bezier_point(
    start: tuple[int, int],
    control_a: tuple[float, float],
    control_b: tuple[float, float],
    end: tuple[int, int],
    progress: float,
) -> tuple[int, int]:
    inverse = 1 - progress
    x = (
        inverse**3 * start[0]
        + 3 * inverse * inverse * progress * control_a[0]
        + 3 * inverse * progress * progress * control_b[0]
        + progress**3 * end[0]
    )
    y = (
        inverse**3 * start[1]
        + 3 * inverse * inverse * progress * control_a[1]
        + 3 * inverse * progress * progress * control_b[1]
        + progress**3 * end[1]
    )
    return round(x), round(y)


def human_like_path(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(distance(start, end), 1)
    normal_x = -dy / length
    normal_y = dx / length
    curve = random.uniform(-0.35, 0.35) * min(length, 180)

    control_a = (
        start[0] + dx * random.uniform(0.20, 0.40) + normal_x * curve,
        start[1] + dy * random.uniform(0.20, 0.40) + normal_y * curve,
    )
    control_b = (
        start[0] + dx * random.uniform(0.60, 0.85) - normal_x * curve * random.uniform(0.4, 0.9),
        start[1] + dy * random.uniform(0.60, 0.85) - normal_y * curve * random.uniform(0.4, 0.9),
    )

    steps = random.randint(28, 70)
    path = []
    for step in range(1, steps + 1):
        progress = smoothstep(step / steps)
        point = bezier_point(start, control_a, control_b, end, progress)
        if 0 < step < steps and random.random() < 0.22:
            point = (point[0] + random.randint(-1, 1), point[1] + random.randint(-1, 1))
        path.append(point)

    return path


def wait_for(seconds: float, expected_position: tuple[int, int]) -> tuple[bool, tuple[int, int]]:
    deadline = sleep_clock.monotonic() + seconds
    latest = expected_position

    while sleep_clock.monotonic() < deadline:
        deadline += pause_for_lock_screen()
        sleep_clock.sleep(min(0.2, max(0, deadline - sleep_clock.monotonic())))
        deadline += pause_for_lock_screen()
        latest = cursor_position()
        if distance(latest, expected_position) > USER_MOVE_TOLERANCE_PIXELS:
            return False, latest

    return True, latest


def move_once(bounds: tuple[int, int, int, int]) -> tuple[bool, tuple[int, int]]:
    start = cursor_position()
    target = pick_target(start, bounds)
    path = human_like_path(start, target)
    expected = start
    duration = random.uniform(0.75, 1.9)
    step_delay = duration / len(path)

    for point in path:
        pause_for_lock_screen()
        current = cursor_position()
        if distance(current, expected) > USER_MOVE_TOLERANCE_PIXELS:
            return False, current

        set_cursor_position(point)
        expected = point
        sleep_clock.sleep(step_delay)

    current = cursor_position()
    if distance(current, expected) > USER_MOVE_TOLERANCE_PIXELS:
        return False, current

    return True, current


def run_auto_movement() -> tuple[int, int]:
    bounds = virtual_screen_bounds()
    log_action("Idle threshold reached. Moving cursor until you move it or the time window ends.")
    expected = cursor_position()

    while active_now():
        moved_by_script, current = move_once(bounds)
        if not moved_by_script:
            log_action("Mouse movement detected. Automatic movement paused.")
            return current

        expected = current
        still_idle, current = wait_for(random.uniform(1.5, 5.0), expected)
        if not still_idle:
            log_action("Mouse movement detected. Automatic movement paused.")
            return current

    log_action("Outside the configured time window. Automatic movement paused.")
    return cursor_position()


def main() -> None:
    log_action("Watching for one minute of mouse idle time. Press Ctrl+C to stop.")
    pause_for_lock_screen()
    last_position = cursor_position()
    last_movement_at = sleep_clock.monotonic()

    try:
        while True:
            last_movement_at += pause_for_lock_screen()
            current = cursor_position()

            if not active_now():
                last_position = current
                last_movement_at = sleep_clock.monotonic()
                sleep_clock.sleep(POLL_SECONDS)
                continue

            if distance(current, last_position) > USER_MOVE_TOLERANCE_PIXELS:
                last_position = current
                last_movement_at = sleep_clock.monotonic()
            elif sleep_clock.monotonic() - last_movement_at >= IDLE_SECONDS:
                last_position = run_auto_movement()
                last_movement_at = sleep_clock.monotonic()

            sleep_clock.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print()
        log_action("Stopped.")


if __name__ == "__main__":
    main()
