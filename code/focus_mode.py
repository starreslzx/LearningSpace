import time


class FocusMode:
    """专注模式管理器 - 用于管理专注计时、时长设置及剩余时间计算"""

    def __init__(self):
        self.is_active = False  # 专注模式是否激活
        self.start_time = None  # 专注开始时间戳
        self.duration = 25 * 60  # 默认专注时长（秒），25分钟
        self.default_durations = [5, 15, 25, 45, 60]  # 默认可选时长（分钟）

    def set_duration(self, minutes):
        """设置专注时长（仅在未激活状态下生效）

        Args:
            minutes (int): 要设置的时长（分钟）

        Returns:
            bool: 设置成功返回True，激活状态下返回False
        """
        if not self.is_active:
            self.duration = minutes * 60
            return True
        return False

    def get_default_durations(self):
        """获取默认可选的专注时长列表

        Returns:
            list: 包含默认时长（分钟）的列表
        """
        return self.default_durations

    def start(self, duration_minutes):
        """启动专注模式，设置并开始计时

        Args:
            duration_minutes (int): 本次专注时长（分钟）
        """
        self.is_active = True
        self.start_time = time.time()
        self.duration = duration_minutes * 60

    def stop(self):
        """停止专注模式，重置计时状态"""
        self.is_active = False
        self.start_time = None
        self.duration = 0

    def get_remaining_time(self):
        """获取当前专注模式的剩余时间（秒）

        Returns:
            float: 剩余秒数（最小为0），未激活时返回0
        """
        if not self.is_active or self.start_time is None:
            return 0

        elapsed = time.time() - self.start_time
        remaining = self.duration - elapsed
        return max(0, remaining)