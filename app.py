# app.py
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import uuid
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['PROCESSED_FOLDER'] = 'processed_files'

# 简易用户系统（生产环境应使用数据库）
USERS = {
    'wxx': '123'
}

# 创建必要目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/video_processing', methods=['GET', 'POST'])
def video_processing():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 处理视频上传
        file = request.files['video']
        if file and allowed_video_file(file.filename):
            # 生成唯一文件名
            unique_id = str(uuid.uuid4())
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{unique_id}_input.mp4')
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], f'{unique_id}_output.mp4')
            
            file.save(input_path)
            
            # 调用原车辆跟踪脚本
            cmd = [
                'python', 
                'main.py',
                '--input', input_path,
                '--output', output_path
            ]
            subprocess.run(cmd)
            
            return render_template('video_result.html', 
                                output_file=output_path,
                                original_file=input_path)
    
    return render_template('video_processing.html')

@app.route('/image_processing', methods=['GET', 'POST'])
def image_processing():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 处理图片上传（需要实现图片处理逻辑）
        file = request.files['image']
        if file and allowed_image_file(file.filename):
            # 图片处理逻辑（需实现）
            pass
    
    return render_template('image_processing.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)