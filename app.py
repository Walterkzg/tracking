from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import subprocess
import uuid
import json

app = Flask(__name__)
app.config.update({
    'UPLOAD_FOLDER': 'D:\\software\\LocalProjects\\VehicleTracking\\uploads',
    'OUTPUT_FOLDER': 'D:\\software\\LocalProjects\\VehicleTracking\\output',
    'MAX_CONTENT_LENGTH': 2 * 1024 * 1024 * 1024  # 2GB
})

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        process_id = uuid.uuid4().hex
        video = request.files['video']
        model = request.files['model']
        
        # 创建存储目录
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(exist_ok=True)
        video_path = upload_dir / f'{process_id}.mp4'
        model_path = upload_dir / f'{process_id}.pt'
        video.save(str(video_path))
        model.save(str(model_path))

        # 启动处理任务
        predict_script = Path(__file__).parent / 'ultralytics' / 'yolo' / 'v8' / 'detect' / 'predict_vis.py'
        cmd = (
            f"python {predict_script} "
            f"model={model_path} "
            f"source={video_path} "
            f"+project={app.config['OUTPUT_FOLDER']} "
            f"+name={process_id} "
            f"save=True"  # 确保保存参数被传递
        )
        subprocess.Popen(cmd, shell=True, cwd=predict_script.parent)
        
        return redirect(url_for('status', process_id=process_id))
    return render_template('upload.html')

@app.route('/status/<process_id>')
def status(process_id):
    return render_template('status.html', process_id=process_id)

@app.route('/progress/<process_id>')
def get_progress(process_id):
    progress_file = Path(app.config['OUTPUT_FOLDER']) / process_id / 'progress.json'
    output_file = Path(app.config['OUTPUT_FOLDER']) / process_id / 'output.mp4'
    
    response = {
        'ready': output_file.exists(),
        'progress': 0,
        'counters': {'enter': {}, 'exit': {}}
    }

    try:
        if progress_file.exists():
            with open(progress_file) as f:
                data = json.load(f)
                response.update({
                    'progress': data.get('percentage', 0),
                    'counters': data.get('counters', {})
                })
    except Exception as e:
        print(f"进度读取错误: {e}")

    return jsonify(response)

@app.route('/download/<process_id>')
def download(process_id):
    return send_from_directory(
        directory=Path(app.config['OUTPUT_FOLDER']) / process_id,
        path='output.mp4',
        as_attachment=True,
        download_name=f'vehicle_analysis_{process_id[:6]}.mp4'
    )

if __name__ == '__main__':
    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
