import cv2
import numpy as np
from typing import Tuple
import random

class TextOverlay:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.4
        self.font_thickness = 1
        
        # Generate random bright colors for different elements
        self.text_color = self._generate_bright_color()
        self.line_color = self._generate_bright_color()
        self.grid_color = self._generate_bright_color()
        
        # Fixed measurements in display order
        self.measurements = [
            ('QUANTUM FLUX', {'min': 0.001, 'max': 9.999, 'unit': 'QF'}),
            ('CONDENSATION', {'min': 20.0, 'max': 99.9, 'unit': '%'}),
            ('TEMPERATURE', {'min': -273.15, 'max': 100.0, 'unit': '°K'})
        ]

    def _generate_bright_color(self):
        """Generate a random bright color"""
        # Generate high values (200-255) for brighter colors
        return tuple(np.random.randint(200, 256, 3).tolist())

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
        
        # Select a random measurement
        name, params = random.choice(self.measurements)
        
        # Calculate the measurement value
        value = float(sum(map(float, rgb_value))) / (255.0 * 3.0)
        value_range = params['max'] - params['min']
        measurement = params['min'] + (value * value_range)
        
        # Draw the selected measurement
        text_y = start_y
        text_x = x
        
        # Draw text
        text = f"{name}: {measurement:.3f} {params['unit']}"
        cv2.putText(display, text, (text_x, text_y), 
                   self.font, self.font_scale, self.text_color, 
                   self.font_thickness, cv2.LINE_AA)
        
        # Get text width for the underline
        (text_width, _) = cv2.getTextSize(text, self.font, self.font_scale, self.font_thickness)[0]
        
        # Draw single line under the text
        final_y = start_y + 25
        cv2.line(display,
                (x - 5, final_y + 5),
                (display.shape[1] - 10, final_y + 5),  # Extends to screen edge
                self.line_color, 1, cv2.LINE_AA)