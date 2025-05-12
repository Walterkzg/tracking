from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import shutil
from datetime import datetime
from main import main as process_video  # 正确导入主函数
import sys
from pathlib import Path
from threading import Thread
from flask_socketio import SocketIO, emit
from flask import jsonify
import cv2

sys.path.append(str(Path(__file__).parent))


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'temp/uploads'
app.config['OUTPUT_FOLDER'] = 'temp/outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB限制

# 添加全局状态变量
processing_status = {
    'is_processing': False,
    'current_frame': 0,
    'total_frames': 0
}

# 简单用户验证（生产环境应使用数据库）
USERS = {'admin': 'admin123'}

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='无效凭证')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# WebSocket路由
@socketio.on('connect')
def handle_connect():
    emit('status_update', processing_status)

@app.route('/video-processing', methods=['GET', 'POST'])
def video_processing():
    global processing_status
    if processing_status['is_processing']:
        return jsonify({'error': '系统正忙，请稍后再试'}), 429

    if request.method == 'POST':
        # 清理旧文件
        shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)
        shutil.rmtree(app.config['OUTPUT_FOLDER'], ignore_errors=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

        # 处理上传文件
        video = request.files['video']
        if video.filename == '':
            return render_template('video_processing.html', error='请选择文件')
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'input_{timestamp}.mp4')
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'output_{timestamp}.mp4')
        
        video.save(input_path)
        
         # 生成唯一任务ID
        job_id = datetime.now().strftime("%Y%m%d%H%M%S")
        processing_status.update({
            'is_processing': True,
            'current_frame': 0,
            'total_frames': 0,
            'job_id': job_id
        })
        # 启动后台线程
        Thread(
            target=process_video_task,
            args=(input_path, output_path, job_id)
        ).start()
    
        return jsonify({
            'message': '已开始处理',
            'job_id': job_id
        }), 202

    return render_template('video_processing.html')
def process_video_task(input_path, output_path, job_id):
    global processing_status
    try:
        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        processing_status['total_frames'] = total_frames
        
        # 正确传递回调函数
        from main import main
        main(
            input_path=input_path,
            output_path=output_path,
            progress_callback=lambda x: update_progress(x, job_id),  # 正确语法
            job_id=job_id
        )
        
    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
    finally:
        processing_status['is_processing'] = False

def update_progress(current_frame, job_id):
    if processing_status['job_id'] == job_id:
        processing_status['current_frame'] = current_frame

@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True
    )

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)