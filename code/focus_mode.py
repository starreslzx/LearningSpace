import time

class FocusMode:
    def __init__(self):
        self.is_active = False
        self.start_time = None
        self.duration = 25 * 60
        self.default_durations = [5, 15, 25, 45, 60]

    def set_duration(self, minutes):
        if not self.is_active:
            self.duration = minutes * 60
            return True
        return False

    def get_default_durations(self):
        return self.default_durations

    def start(self, duration_minutes):
        self.is_active = True
        self.start_time = time.time()
        self.duration = duration_minutes * 60

    def stop(self):
        self.is_active = False
        self.start_time = None
        self.duration = 0

    def get_remaining_time(self):
        if not self.is_active or self.start_time is None:
            return 0

        elapsed = time.time() - self.start_time
        remaining = self.duration - elapsed
        return max(0, remaining)