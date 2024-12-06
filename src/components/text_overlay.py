import cv2
import numpy as np
from typing import Tuple

class TextOverlay:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.4
        self.font_thickness = 1
        self.text_color = (255, 255, 255)  # White text
        self.line_color = (128, 128, 128)  # Gray line
        
        # Fixed measurements in display order
        self.measurements = [
            ('QUANTUM FLUX', {'min': 0.001, 'max': 9.999, 'unit': 'QF'}),
            ('CONDENSATION', {'min': 20.0, 'max': 99.9, 'unit': '%'}),
            ('TEMPERATURE', {'min': -273.15, 'max': 100.0, 'unit': '°K'})
        ]

    def render(self, display: np.ndarray, text: str, position: Tuple[int, int], 
               rotation: int = 0, display_width: int = None, display_height: int = None) -> None:
        """Render text overlay"""
        x, y = position
        
        # Sample RGB value from the container position
        try:
            rgb_value = display[y, x]
        except IndexError:
            rgb_value = (0, 0, 0)
            
        # Draw measurements above container
        start_y = max(y - 60, 10)  # Start 60 pixels above container, minimum 10px from top
        
        for i, (name, params) in enumerate(self.measurements):
            value = float(sum(map(float, rgb_value))) / (255.0 * 3.0)  # Normalized 0-1
            value_range = params['max'] - params['min']
            measurement = params['min'] + (value * value_range)
            
            text = f"{name}: {measurement:.3f} {params['unit']}"
            text_y = start_y + (i * 15)  # 15 pixels between each line
            
            cv2.putText(display, text, (x, text_y), 
                       self.font, self.font_scale, self.text_color, 
                       self.font_thickness, cv2.LINE_AA)