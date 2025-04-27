import cv2

class VideoHandler:
    def __init__(self, input_path, output_path=None):
        self.cap = cv2.VideoCapture(input_path)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if output_path:
            self.writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*'mp4v'),
                self.fps,
                (self.width, self.height)
            )
        else:
            self.writer = None
    
    def release(self):
        self.cap.release()
        if self.writer:
            self.writer.release()
    
    def write_frame(self, frame):
        if self.writer:
            self.writer.write(frame)