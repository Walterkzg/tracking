from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import subprocess
import uuid
import threading

# YOLOv8 Flask Web App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'D:\\software\\LocalProjects\\VehicleTracking\\uploads'
app.config['OUTPUT_FOLDER'] = 'D:\\software\\LocalProjects\\VehicleTracking\\output'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB限制

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # 生成唯一标识符
        process_id = uuid.uuid4().hex
        
        # 保存上传文件
        video = request.files['video']
        model = request.files['model']
        
        # 创建存储目录
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{process_id}.mp4')
        model_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{process_id}.pt')
        video.save(video_path)
        model.save(model_path)

        # 计算predict_vis.py的绝对路径
        predict_vis_path = Path(__file__).parent / "ultralytics" / "yolo" / "v8" / "detect" / "predict_vis.py"
        working_dir = predict_vis_path.parent

        # 执行检测命令
        # 在app.py中构建命令时添加验证
        cmd = (
            f"python {predict_vis_path.name} "
            f"model={model_path} "
            f"source={video_path} "
            f"+project={app.config['OUTPUT_FOLDER']} "
            f"+name={process_id} "
            f"save=True"  # 确保保存参数被传递
        )
        subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(working_dir)  # 关键设置
            )

        return redirect(url_for('status', process_id=process_id))
    return render_template('upload.html')

@app.route('/status/<process_id>')
def status(process_id):
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], process_id, 'output.mp4')
    return render_template('status.html', 
                         ready=os.path.exists(output_path),
                         process_id=process_id)

@app.route('/download/<process_id>')
def download(process_id):
    directory = os.path.join(app.config['OUTPUT_FOLDER'], process_id)
    return send_from_directory(directory, '{process_id}.mp4', as_attachment=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
