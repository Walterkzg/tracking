from ultralytics import YOLO
from .base_tracker import BaseTracker

class YOLOv8Tracker(BaseTracker):
    def __init__(self, model_path, config):
        super().__init__(config)
        self.model = YOLO(model_path)
    
    def update(self, frame):
        # 执行跟踪（persist保持跨帧ID，verbose关闭控制台输出）
        results = self.model.track(
            frame,
            persist=True,
            tracker=f"{self.config['tracker_type']}.yaml",
            conf=self.config['conf_threshold'],
            iou=self.config['iou_threshold'],
            classes=self.config['classes']['vehicles'],
            verbose=False
        )
        
        # 提取跟踪结果
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            # 更新每个目标的轨迹
            for box, track_id in zip(boxes, track_ids):
                center = (int(box[0]), int(box[1]))  # 中心坐标(x,y)
                self._update_history(track_id, center)
        
        return results