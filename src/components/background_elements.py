import cv2
import numpy as np
import random

class BackgroundElements:
    def __init__(self):
        self.grid_position = 0
        self.grid_speed = 1  # Reduced speed of grid movement
        self.grid_color = (255, 255, 255)  # White color
        self.grid_spacing = random.randint(10, 20)
        self.grid_opacity = 0.1  # Set opacity to 10%

    def render(self, display: np.ndarray) -> None:
        self._draw_moving_grid(display)

    def _draw_moving_grid(self, display: np.ndarray):
        h, w = display.shape[:2]
        spacing = self.grid_spacing
        color = self.grid_color
        opacity = self.grid_opacity
        
        overlay = display.copy()
        self.grid_position = (self.grid_position + self.grid_speed) % spacing
        
        # Draw vertical lines
        for x in range(-spacing, w, spacing):
            cv2.line(overlay, (x + self.grid_position, 0), (x + self.grid_position, h), color, 1, cv2.LINE_AA)
        
        # Draw horizontal lines
        for y in range(-spacing, h, spacing):
            cv2.line(overlay, (0, y + self.grid_position), (w, y + self.grid_position), color, 1, cv2.LINE_AA)
        
        cv2.addWeighted(overlay, opacity, display, 1 - opacity, 0, display)