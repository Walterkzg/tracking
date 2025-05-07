import cv2
from src.tracker.yolov8_tracker import YOLOv8Tracker
from src.utils.visualization import draw_detections, draw_trails
from src.utils.video_utils import VideoHandler
from configs import load_config  # 现在可以正确导入了
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, help='Input video path')
    parser.add_argument('--output', type=str, help='Output video path')
    return parser.parse_args()
def main():
    # 加载配置
    config = load_config("D:\\vscode\\ai-project\\Vehicle-Tracking\\configs\\tracking.yaml")
    
    # 初始化跟踪器
    tracker = YOLOv8Tracker(
        model_path="models/yolov8n.pt",
        config=config
    )
    
    # 视频处理
    video = VideoHandler(
        input_path="D:\\vscode\\ai-project\\Vehicle-Tracking\\data\\input\\test.mp4",
        output_path="D:\\vscode\\ai-project\\Vehicle-Tracking\\data\\output\\output.mp4"
    )
    
    while True:
        ret, frame = video.cap.read()
        if not ret:
            break
    
    # 执行跟踪
        results = tracker.update(frame)
    
    # 可视化
        if results[0].boxes.id is not None:
        # 绘制检测框（使用轨迹相同的颜色）
            colors = draw_trails(frame, tracker.track_history, config)
            for box, track_id in zip(results[0].boxes, results[0].boxes.id.int().cpu().tolist()):
                color = colors.get(track_id, (0,255,0))  # 默认绿色
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                cv2.putText(frame, f"ID:{track_id}", (x1,y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # 显示帧率信息
        fps = video.cap.get(cv2.CAP_PROP_FPS)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
    
        cv2.imshow("Optimized Tracking", frame)
        video.write_frame(frame)
    
        if cv2.waitKey(1) == ord('q'):
            break
    
    # 释放资源
    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    args = parse_args()
    # 修改VideoHandler的路径为参数传入的路径
    video = VideoHandler(
        input_path=args.input,
        output_path=args.output
    )
    main()