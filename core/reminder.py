import threading
import time
import datetime
import os
import sys


def _get_icon_path():
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "icon.ico")


def send_notification():
    try:
        from winotify import Notification, audio
        icon_path = _get_icon_path()
        toast = Notification(
            app_id="Daily Task Log",
            title="Time to log your tasks!",
            msg="Don't forget to record what you worked on today.",
            icon=icon_path if os.path.exists(icon_path) else "",
            duration="long",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.add_actions(label="Open Log", launch="dailytasklog://open")
        toast.show()
    except Exception as e:
        print(f"Notification error: {e}")


class ReminderThread(threading.Thread):
    def __init__(self, get_config_fn, show_window_fn):
        super().__init__(daemon=True)
        self.get_config = get_config_fn
        self.show_window = show_window_fn
        self._stop_event = threading.Event()
        self._last_fired_date = None

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            try:
                cfg = self.get_config()
                if cfg.get("reminder_enabled", True):
                    now = datetime.datetime.now()
                    today = now.date()
                    reminder_str = cfg.get("reminder_time", "17:30")
                    hour, minute = map(int, reminder_str.split(":"))
                    fire_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if (
                        now >= fire_time
                        and self._last_fired_date != today
                        and (now - fire_time).total_seconds() < 120
                    ):
                        self._last_fired_date = today
                        send_notification()
            except Exception as e:
                print(f"Reminder loop error: {e}")
            self._stop_event.wait(60)


def create_tray_icon(show_fn, quit_fn, get_config_fn):
    try:
        import pystray
        from PIL import Image, ImageDraw

        def _make_icon():
            icon_path = _get_icon_path()
            if os.path.exists(icon_path):
                return Image.open(icon_path).resize((64, 64))
            img = Image.new("RGBA", (64, 64), (24, 95, 165, 255))
            d = ImageDraw.Draw(img)
            d.rectangle([16, 20, 48, 44], fill=(255, 255, 255))
            d.rectangle([20, 24, 44, 28], fill=(24, 95, 165))
            d.rectangle([20, 32, 44, 36], fill=(24, 95, 165))
            d.rectangle([20, 40, 32, 44], fill=(24, 95, 165))
            return img

        menu = pystray.Menu(
            pystray.MenuItem("Open Daily Task Log", show_fn, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", quit_fn),
        )
        icon = pystray.Icon("DailyTaskLog", _make_icon(), "Daily Task Log", menu)
        return icon
    except Exception as e:
        print(f"Tray error: {e}")
        return None
