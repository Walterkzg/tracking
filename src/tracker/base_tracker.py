from abc import ABC, abstractmethod
from collections import defaultdict

class BaseTracker(ABC):
    def __init__(self, config):
        self.config = config
        self.track_history = defaultdict(list)
    
    @abstractmethod
    def update(self, frame):
        """输入帧图像，返回跟踪结果"""
        pass
    
    def _update_history(self, track_id, center):
        """更新轨迹历史"""
        self.track_history[track_id].append(center)
        # 限制历史长度
        if len(self.track_history[track_id]) > self.config['max_trail_length']:
            self.track_history[track_id].pop(0)