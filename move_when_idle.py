"""Move the Windows cursor after configured keyboard/mouse idle time.

No clicks are sent. Press Ctrl+C in the terminal to stop the script.
"""

from __future__ import annotations

import ctypes
import json
import math
import random
import sys
import time as sleep_clock
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path


DESKTOP_SWITCHDESKTOP = 0x0100
CONFIG_PATH = Path(__file__).with_name("move_when_idle_config.json")

DEFAULT_CONFIG = {
    "idle_seconds": 60,
    "poll_seconds": 0.5,
    "lock_poll_seconds": 1.0,
    "lock_status_log_seconds": 60,
    "user_move_tolerance_pixels": 4,
    "log_include_date": False,
    "active_windows": [
        {"start": "08:00", "end": "12:00"},
        {"start": "13:12", "end": "18:00"},
    ],
}


@dataclass(frozen=True)
class AppConfig:
    idle_seconds: float
    poll_seconds: float
    lock_poll_seconds: float
    lock_status_log_seconds: float
    user_move_tolerance_pixels: int
    log_include_date: bool
    active_windows: tuple[tuple[time, time], ...]


def parse_positive_number(config: dict[str, object], key: str) -> float:
    value = config.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{key} must be a positive number.")
    return float(value)


def parse_positive_int(config: dict[str, object], key: str) -> int:
    value = config.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{key} must be a positive integer.")
    return value


def parse_time_value(value: object, key: str) -> time:
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a time string in HH:MM format.")

    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as error:
        raise ValueError(f"{key} must be a time string in HH:MM format.") from error


def parse_active_windows(value: object) -> tuple[tuple[time, time], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("active_windows must be a non-empty list.")

    active_windows = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"active_windows item {index} must be an object.")

        start = parse_time_value(item.get("start"), f"active_windows item {index} start")
        end = parse_time_value(item.get("end"), f"active_windows item {index} end")
        if start >= end:
            raise ValueError(f"active_windows item {index} start must be before end.")

        active_windows.append((start, end))

    return tuple(active_windows)


def load_config(path: Path) -> AppConfig:
    config = DEFAULT_CONFIG.copy()
    if path.exists():
        try:
            loaded_config = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise SystemExit(f"Could not read {path.name}: {error}") from error
        except json.JSONDecodeError as error:
            raise SystemExit(f"Could not parse {path.name}: {error}") from error

        if not isinstance(loaded_config, dict):
            raise SystemExit(f"{path.name} must contain a JSON object.")
        config.update(loaded_config)

    try:
        log_include_date = config.get("log_include_date")
        if not isinstance(log_include_date, bool):
            raise ValueError("log_include_date must be true or false.")

        return AppConfig(
            idle_seconds=parse_positive_number(config, "idle_seconds"),
            poll_seconds=parse_positive_number(config, "poll_seconds"),
            lock_poll_seconds=parse_positive_number(config, "lock_poll_seconds"),
            lock_status_log_seconds=parse_positive_number(config, "lock_status_log_seconds"),
            user_move_tolerance_pixels=parse_positive_int(config, "user_move_tolerance_pixels"),
            log_include_date=log_include_date,
            active_windows=parse_active_windows(config.get("active_windows")),
        )
    except ValueError as error:
        raise SystemExit(f"Invalid {path.name}: {error}") from error


if sys.platform != "win32":
    raise SystemExit("This script uses the Windows cursor API and must run on Windows.")


CONFIG = load_config(CONFIG_PATH)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class Point(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class LastInputInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


@dataclass(frozen=True)
class DesktopStatus:
    available: bool
    stage: str
    error_code: int


user32.GetCursorPos.argtypes = [ctypes.POINTER(Point)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LastInputInfo)]
user32.GetLastInputInfo.restype = wintypes.BOOL
user32.OpenDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.OpenDesktopW.restype = wintypes.HANDLE
user32.SwitchDesktop.argtypes = [wintypes.HANDLE]
user32.SwitchDesktop.restype = wintypes.BOOL
user32.CloseDesktop.argtypes = [wintypes.HANDLE]
user32.CloseDesktop.restype = wintypes.BOOL
kernel32.GetTickCount.argtypes = []
kernel32.GetTickCount.restype = wintypes.DWORD

try:
    user32.SetProcessDPIAware()
except AttributeError:
    pass


def active_now() -> bool:
    current = datetime.now().time()
    return any(start <= current < end for start, end in CONFIG.active_windows)


def log_action(message: str) -> None:
    timestamp_format = "%Y-%m-%d %H:%M:%S" if CONFIG.log_include_date else "%H:%M:%S"
    print(f"[{datetime.now():{timestamp_format}}] {message}", flush=True)


def default_desktop_status() -> DesktopStatus:
    ctypes.set_last_error(0)
    desktop = user32.OpenDesktopW("Default", 0, False, DESKTOP_SWITCHDESKTOP)
    if not desktop:
        return DesktopStatus(False, "OpenDesktopW", ctypes.get_last_error())

    try:
        ctypes.set_last_error(0)
        if user32.SwitchDesktop(desktop):
            return DesktopStatus(True, "SwitchDesktop", 0)
        return DesktopStatus(False, "SwitchDesktop", ctypes.get_last_error())
    finally:
        user32.CloseDesktop(desktop)


def default_desktop_available() -> bool:
    return default_desktop_status().available


def pause_for_lock_screen() -> float:
    status = default_desktop_status()
    if status.available:
        return 0.0

    log_action(
        "Windows desktop unavailable, possibly locked. "
        f"Pausing. {status.stage} error: {status.error_code}."
    )
    paused_at = sleep_clock.monotonic()
    last_status_log_at = paused_at

    while True:
        sleep_clock.sleep(CONFIG.lock_poll_seconds)
        status = default_desktop_status()
        if status.available:
            paused_for = sleep_clock.monotonic() - paused_at
            log_action("Windows desktop available. Resuming.")
            return paused_for

        now = sleep_clock.monotonic()
        if now - last_status_log_at >= CONFIG.lock_status_log_seconds:
            log_action(f"Still paused. {status.stage} error: {status.error_code}.")
            last_status_log_at = now


def last_input_tick_count() -> int:
    info = LastInputInfo()
    info.cbSize = ctypes.sizeof(LastInputInfo)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(info.dwTime)


def seconds_since_last_input() -> float:
    elapsed_ms = ctypes.c_uint32(int(kernel32.GetTickCount()) - last_input_tick_count()).value
    return elapsed_ms / 1000


def input_changed_since(last_seen_tick: int) -> bool:
    return last_input_tick_count() != last_seen_tick


def cursor_position() -> tuple[int, int]:
    while True:
        pause_for_lock_screen()
        point = Point()
        if user32.GetCursorPos(ctypes.byref(point)):
            return point.x, point.y
        error_code = ctypes.get_last_error()
        if default_desktop_available():
            raise ctypes.WinError(error_code)


def set_cursor_position(position: tuple[int, int]) -> None:
    x, y = position
    while True:
        pause_for_lock_screen()
        if user32.SetCursorPos(int(x), int(y)):
            return
        error_code = ctypes.get_last_error()
        if default_desktop_available():
            raise ctypes.WinError(error_code)


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
    last_seen_input = last_input_tick_count()

    while sleep_clock.monotonic() < deadline:
        deadline += pause_for_lock_screen()
        sleep_clock.sleep(min(0.2, max(0, deadline - sleep_clock.monotonic())))
        deadline += pause_for_lock_screen()
        latest = cursor_position()
        if input_changed_since(last_seen_input):
            return False, latest
        if distance(latest, expected_position) > CONFIG.user_move_tolerance_pixels:
            return False, latest

    return True, latest


def move_once(bounds: tuple[int, int, int, int]) -> tuple[bool, tuple[int, int]]:
    start = cursor_position()
    target = pick_target(start, bounds)
    path = human_like_path(start, target)
    expected = start
    duration = random.uniform(0.75, 1.9)
    step_delay = duration / len(path)
    last_seen_input = last_input_tick_count()

    for point in path:
        pause_for_lock_screen()
        current = cursor_position()
        if input_changed_since(last_seen_input):
            return False, current
        if distance(current, expected) > CONFIG.user_move_tolerance_pixels:
            return False, current

        set_cursor_position(point)
        expected = point
        last_seen_input = last_input_tick_count()
        sleep_clock.sleep(step_delay)

    current = cursor_position()
    if input_changed_since(last_seen_input):
        return False, current
    if distance(current, expected) > CONFIG.user_move_tolerance_pixels:
        return False, current

    return True, current


def run_auto_movement() -> tuple[int, int]:
    bounds = virtual_screen_bounds()
    log_action("Idle threshold reached. Moving cursor until you move it or the time window ends.")
    expected = cursor_position()

    while active_now():
        moved_by_script, current = move_once(bounds)
        if not moved_by_script:
            log_action("User input detected. Automatic movement paused.")
            return current

        expected = current
        still_idle, current = wait_for(random.uniform(1.5, 5.0), expected)
        if not still_idle:
            log_action("User input detected. Automatic movement paused.")
            return current

    log_action("Outside the configured time window. Automatic movement paused.")
    return cursor_position()


def main() -> None:
    log_action(
        f"Watching for {CONFIG.idle_seconds:g} seconds of keyboard/mouse idle time. "
        "Press Ctrl+C to stop."
    )
    pause_for_lock_screen()

    try:
        while True:
            pause_for_lock_screen()

            if not active_now():
                sleep_clock.sleep(CONFIG.poll_seconds)
                continue

            if seconds_since_last_input() >= CONFIG.idle_seconds:
                run_auto_movement()

            sleep_clock.sleep(CONFIG.poll_seconds)
    except KeyboardInterrupt:
        print()
        log_action("Stopped.")


if __name__ == "__main__":
    main()
