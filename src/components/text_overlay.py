import cv2
import numpy as np
from typing import Tuple

class TextOverlay:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 1
        self.text_color = (255, 255, 255)
        self.line_color = (128, 128, 128)
        
    def render(self, display: np.ndarray, text: str, position: Tuple[int, int], 
               rotation: int = 0, display_width: int = None, display_height: int = None) -> None:
        """Render text with line overlay"""
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.font, self.font_scale, self.font_thickness)
        
        x, y = position
        
        # Draw based on rotation
        if rotation == 0:
            # Text above, with line extending to right edge
            text_y = max(y - 20, 10)
            cv2.putText(display, text, (x, text_y), 
                       self.font, self.font_scale, self.text_color, 
                       self.font_thickness, cv2.LINE_AA)
            cv2.line(display, (x, text_y + 5), 
                    (display_width, text_y + 5), self.line_color, 1)
            
        elif rotation == 90:
            # Vertical text on the left
            text_x = max(x - 20, 10)
            cv2.putText(display, text, (text_x, y), 
                       self.font, self.font_scale, self.text_color, 
                       self.font_thickness, cv2.LINE_AA)
            cv2.line(display, (text_x + 5, y), 
                    (text_x + 5, display_height), self.line_color, 1)
            
        elif rotation == 180:
            # Text below, reversed
            text_y = min(y + text_height + 25, display_height - 10)
            text_start = x - text_width
            cv2.putText(display, text[::-1], (text_start, text_y), 
                       self.font, self.font_scale, self.text_color, 
                       self.font_thickness, cv2.LINE_AA)
            cv2.line(display, (0, text_y + 5), 
                    (text_start + text_width, text_y + 5), self.line_color, 1)
            
        else:  # 270 degrees
            # Vertical text on the right
            text_x = min(x + 25, display_width - 10)
            cv2.putText(display, text[::-1], (text_x, y), 
                       self.font, self.font_scale, self.text_color, 
                       self.font_thickness, cv2.LINE_AA)
            cv2.line(display, (text_x - 5, 0), 
                    (text_x - 5, y), self.line_color, 1) 