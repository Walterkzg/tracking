class SpeedCalculator:
    def __init__(self, fps, pixels_per_meter=50):
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        self.prev_positions = {}
    
    def calculate(self, track_id, current_pos):
        if track_id in self.prev_positions:
            prev_pos = self.prev_positions[track_id]
            distance_pixels = ((current_pos[0]-prev_pos[0])**2 + 
                              (current_pos[1]-prev_pos[1])**2)**0.5
            speed_mps = (distance_pixels/self.pixels_per_meter) * self.fps
            speed_kph = speed_mps * 3.6
            return speed_kph
        self.prev_positions[track_id] = current_pos
        return 0