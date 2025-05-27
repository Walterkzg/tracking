#conda activate gradio3.10 
#cd /mnt/f/YOLOv8-DeepSORT-Object-Tracking/ultralytics/yolo/v8/detect
#python /mnt/f/YOLOv8-DeepSORT-Object-Tracking/flask/app.py
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
import shutil
import uuid
import subprocess
from pathlib import Path

app = Flask(__name__, static_folder='img')

app.config['UPLOAD_FOLDER'] = '/mnt/f/YOLOv8-DeepSORT-Object-Tracking/inputs'
app.config['OUTPUT_FOLDER'] = '/mnt/f/YOLOv8-DeepSORT-Object-Tracking/runs/detect/train'
app.config['MAX_CONTENT_LENGTH'] = 2000 * 1024 * 1024  # 2000 MB
# 路径定义
PREDICT_SCRIPT = "/mnt/f/YOLOv8-DeepSORT-Object-Tracking/ultralytics/yolo/v8/detect/predict_count copy.py"
BEST_WEIGHTS = "/mnt/f/YOLOv8-DeepSORT-Object-Tracking/ultralytics/yolo/v8/detect/best.pt"
def run_detection(video_path):
    global progress_data
    command = [
        "python", PREDICT_SCRIPT,
        f"model={BEST_WEIGHTS}",
        f"source={video_path}",
        "save=True",
        "conf=0.5",
        f"+project={OUTPUT_FOLDER}"
    ]

from flask import jsonify



@app.route("/progress")
def progress():
    return jsonify(progress_data)

# 用于访问背景图
@app.route("/img/<path:filename>")
def send_image(filename):
    return send_from_directory("img", filename)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "video" not in request.files:
            return "No file part", 400

        file = request.files["video"]
        if file.filename == "":
            return "No selected file", 400

        # 保存上传文件
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        video_id = uuid.uuid4().hex
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}.mp4")
        file.save(input_path)

        # 清空旧输出
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        if output_dir.exists():
            shutil.rmtree(output_dir)

        # 执行预测命令
        command = [
            "python", PREDICT_SCRIPT,
            f"model={BEST_WEIGHTS}",
            f"source={input_path}",
            "save=True",
            "conf=0.5",
            f"+project={'/mnt/f/YOLOv8-DeepSORT-Object-Tracking/runs/detect'}"
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        print("=== predict.py 输出日志 ===")
        print(result.stdout)
        print("=== 错误信息（如果有） ===")
        print(result.stderr)

        if result.returncode != 0:
            return f"模型执行失败：\n{result.stderr}", 500

        # 查找输出视频并进行转码
        output_video = ""
        for f in output_dir.glob("*.mp4"):
            raw_output_path = str(f)
            output_video = f"converted_{uuid.uuid4().hex}.mp4"
            converted_path = os.path.join(app.config['OUTPUT_FOLDER'], output_video)

            # ffmpeg 转码为浏览器兼容格式
            command_ffmpeg = [
                "ffmpeg",
                "-i", raw_output_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-movflags", "+faststart",
                "-y",  # 覆盖输出
                converted_path
            ]
            subprocess.run(command_ffmpeg, check=True)

            break

        if not output_video:
            return "未能找到处理后的视频文件", 500

        # 这里不要直接跳转播放视频，改跳转到展示中间图片页面
        return redirect(url_for("show_images", filename=output_video))

    return render_template("index.html")

#检查图片有没有生成
@app.route("/check_images")
def check_images():
    image_folder = Path("/mnt/f/YOLOv8-DeepSORT-Object-Tracking/img0")
    images = list(image_folder.glob("*.jpg"))
    return jsonify({"ready": len(images) >0})
#Flask 路由展示这些图片
@app.route("/img0/<path:filename>")
def send_output_image(filename):
    return send_from_directory("/mnt/f/YOLOv8-DeepSORT-Object-Tracking/img0", filename)
@app.route("/show_images")
def show_images():
    image_folder = Path("/mnt/f/YOLOv8-DeepSORT-Object-Tracking/img0")
    images = [f.name for f in sorted(image_folder.glob("*.jpg"))]
    return render_template("show_images.html", images=images)
@app.route("/get_images")
def get_images():
    image_folder = Path("/mnt/f/YOLOv8-DeepSORT-Object-Tracking/img0")
    images = sorted(f.name for f in image_folder.glob("*.jpg"))
    return jsonify({"images": images})

@app.route("/check_video")
def check_video():
    output_dir = Path("/mnt/f/YOLOv8-DeepSORT-Object-Tracking/runs/detect/train") 
    for f in output_dir.glob("converted_*.mp4"):
        return jsonify({"ready": True, "filename": f.name})
    return jsonify({"ready": False})


@app.route("/play/<filename>")
def play_video(filename):
    return render_template("play.html", filename=filename)

@app.route("/video/<filename>")
def get_video(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
