import gradio as gr
import cv2
import tempfile
from pathlib import Path
from ultralytics import YOLO
import torch
import numpy as np

# 初始化模型
model = YOLO('Vehicle-Tracking/models/yolov8n.pt').to('cuda' if torch.cuda.is_available() else 'cpu')

def process_video(input_video):
    # 初始化轨迹历史（每次处理新视频时重置）
    track_history = {}
    
    # 创建临时输出文件
    output_path = Path(tempfile.mktemp(suffix=".mp4"))
    
    # 打开视频文件
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    # 处理每一帧
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        try:
            # 执行跟踪（添加imgsz参数确保输入尺寸稳定）
            results = model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=0.4,
                iou=0.5,
                classes=[2, 3, 5, 7],
                imgsz=640,
                verbose=False
            )
            
            # 安全获取结果
            if len(results) == 0 or results[0].boxes.id is None:
                out.write(frame)
                continue
                
            # 转换为CPU tensor处理
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            # 维度验证
            if boxes.shape[0] != len(track_ids):
                print(f"维度不匹配: boxes {boxes.shape}, ids {len(track_ids)}")
                out.write(frame)
                continue
                
            # 更新轨迹历史
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                
                if track_id not in track_history:
                    track_history[track_id] = []
                track_history[track_id].append(center)
                
                # 保持轨迹长度
                if len(track_history[track_id]) > 30:
                    track_history[track_id].pop(0)
                
                # 绘制检测框
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID:{track_id}", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 绘制轨迹
            for track_id, trail in track_history.items():
                if len(trail) > 1:
                    points = np.array(trail, dtype=np.int32)
                    cv2.polylines(frame, [points], False, (0, 0, 255), 2)
        
        except Exception as e:
            print(f"帧处理错误: {str(e)}")
        
        # 写入输出帧
        out.write(frame)
    
    # 释放资源
    cap.release()
    out.release()
    
    return str(output_path)

# 创建Gradio界面
demo = gr.Interface(
    fn=process_video,
    inputs=gr.Video(label="上传监控视频"),
    outputs=gr.Video(label="追踪结果"),
    title="实时车辆追踪系统",
    examples=[["D:\\vscode\\ai-project\\Vehicle-Tracking\\data\\input\\test.mp4"]],
    allow_flagging="never"
)


# 运行界面
if __name__ == "__main__":
    demo.launch(share=True)  # 设置share=False仅本地访问