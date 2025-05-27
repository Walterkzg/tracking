import os
import uuid
import subprocess
import threading
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'D:\\software\\LocalProjects\\VehicleTracking\\uploads'
app.config['OUTPUT_FOLDER'] = 'D:\\software\\LocalProjects\\VehicleTracking\\output'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

# 确保上传和输出目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def run_detection(process_id, model_path, video_path):
    """后台运行检测任务的函数"""
    try:
        predict_vis_path = Path(__file__).parent / "ultralytics" / "yolo" / "v8" / "detect" / "predict_vis.py"
        working_dir = predict_vis_path.parent
        
        cmd = [
            "python", str(predict_vis_path),
            f"model={model_path}",
            f"source={video_path}",
            f"project={app.config['OUTPUT_FOLDER']}",
            f"name={process_id}",
            "save=True"
        ]
        
        subprocess.run(cmd, cwd=str(working_dir), check=True)
    except Exception as e:
        app.logger.error(f"检测任务失败: {str(e)}")

@app.route('/')
def upload_page():
    """上传页面"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    """处理文件上传"""
    if 'model' not in request.files or 'video' not in request.files:
        return jsonify({'error': '缺少文件'}), 400
        
    model = request.files['model']
    video = request.files['video']
    
    # 生成唯一任务ID
    process_id = uuid.uuid4().hex
    model_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{process_id}.pt')
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{process_id}.mp4')
    
    # 保存文件
    model.save(model_path)
    video.save(video_path)
    
    # 启动后台任务
    threading.Thread(
        target=run_detection,
        args=(process_id, model_path, video_path),
        daemon=True
    ).start()
    
    return jsonify({
        'status': 'processing',
        'process_id': process_id,
        'redirect': url_for('status_page', process_id=process_id)
    })

@app.route('/status/<process_id>')
def status_page(process_id):
    """状态页面"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX请求返回JSON状态
        frame_dir = Path(app.config['OUTPUT_FOLDER']) / process_id / 'frames'
        ready = (Path(app.config['OUTPUT_FOLDER']) / process_id / 'output.mp4').exists()
        
        return jsonify({
            'ready': ready,
            'processed_frames': len(list(frame_dir.glob('frame_*.jpg'))) if frame_dir.exists() else 0,
            'total_frames': 0  # 实际应用中可以从视频获取总帧数
        })
    
    # 普通请求返回HTML页面
    return render_template('status.html', process_id=process_id)

@app.route('/frame/<process_id>/<int:frame_num>')  # 注意这里是frame不是frames
def get_frame(process_id, frame_num):
    """确保此路由与前端请求URL完全一致"""
    frame_dir = Path(app.config['OUTPUT_FOLDER']) / process_id / 'frames'
    frame_path = frame_dir / f'frame_{frame_num:04d}.jpg'  # 匹配实际文件名格式
    
    # 调试输出
    print(f"查找帧: {frame_path} | 是否存在: {frame_path.exists()}")
    
    if not frame_path.exists():
        # 返回空白图像或404
        from flask import make_response
        return make_response('', 404)
    
    return send_from_directory(frame_dir, frame_path.name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
