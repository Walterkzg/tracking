该项目是成都信息工程大学2022级人工智能221第1小组的作品--车辆跟踪并技术项目
该项目使用yolov8+deepsort进行目标检测，使用flask连接前后端，使用html作为前端。
使用项目步骤：
1.创建一个专门的虚拟环境（以防包冲突） 使用!pip install -e '.[dev]'命令调用setup.py下载对应的包 并且将ultralytics这个文件夹模块化。
2.在终端使用如下命令即可启动系统：
conda activate gradio3.10 
cd /mnt/f/YOLOv8-DeepSORT-Object-Tracking/ultralytics/yolo/v8/detect（根据对应电脑的detect的绝对路径而改变）
python /mnt/f/YOLOv8-DeepSORT-Object-Tracking/flask/app.py
