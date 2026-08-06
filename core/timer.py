import time
from typing import Optional
from aqt.qt import QObject, QTimer, pyqtSignal


class SessionTimer(QObject):
    tick = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.start_time: Optional[float] = None
        self._qtimer = QTimer()
        self._qtimer.timeout.connect(self._on_tick)
        self._enabled = True

    def start(self):
        self.start_time = time.time()
        if self._enabled:
            self._qtimer.start(1000)

    def stop(self):
        self._qtimer.stop()
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.start_time = None
            return elapsed
        return 0

    def pause(self):
        self._qtimer.stop()

    def resume(self):
        if self._enabled and self.start_time:
            self._qtimer.start(1000)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled and self.start_time:
            self._qtimer.start(1000)
        else:
            self._qtimer.stop()

    def elapsed_seconds(self) -> int:
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

    def _on_tick(self):
        if self.start_time:
            self.tick.emit(self.elapsed_seconds())
