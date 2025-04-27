import cv2
import numpy as np

def draw_detections(frame, results, config):
    """绘制检测框和ID"""
    viz_config = config.get('visualization', {})  # 安全获取可视化配置
    
    for box, track_id in zip(results[0].boxes, results[0].boxes.id.int().cpu().tolist()):
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        # 绘制矩形框
        cv2.rectangle(
            frame, 
            (x1, y1), (x2, y2),
            color=(0, 255, 0),
            thickness=viz_config.get('box_thickness', 2)
        )
        
        # 构建显示文本
        text = f"ID:{track_id}"
        if viz_config.get('show_conf', False):
            text += f" {box.conf[0]:.2f}"
        
        # 显示文本
        if viz_config.get('show_ids', True):
            cv2.putText(
                frame, text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0),
                1, cv2.LINE_AA
            )
    
    return frame

def draw_trails(frame, track_history, config):
    current_colors = {}  # 存储当前活跃目标的颜色
    
    for track_id, trail in list(track_history.items()):
        # 动态计算颜色（根据ID哈希值）
        color_idx = track_id % 10  # 使用10种预设颜色
        color = [
            (255,0,0), (0,255,0), (0,0,255),
            (255,255,0), (0,255,255), (255,0,255),
            (128,128,0), (0,128,128), (128,0,128),
            (64,64,64)
        ][color_idx]
        current_colors[track_id] = color
        
        # 只绘制最近N个点
        max_points = config.get('max_trail_points', 20)
        recent_trail = trail[-max_points:]
        
        # 绘制连续轨迹线（带透明度效果）
        overlay = frame.copy()
        for i in range(1, len(recent_trail)):
            cv2.line(
                overlay, recent_trail[i-1], recent_trail[i],
                color=color,
                thickness=2
            )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    return current_colors  # 返回当前使用的颜色