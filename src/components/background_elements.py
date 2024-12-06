import cv2
import numpy as np
from typing import Tuple
import random

class BackgroundElements:
    def __init__(self):
        self.elements = []
        self.generate_elements()
        
    def _generate_bright_color(self):
        return tuple(np.random.randint(200, 256, 3).tolist())
        
    def generate_elements(self):
        self.elements = [
            {
                'type': 'grid',
                'color': self._generate_bright_color(),
                'spacing': random.randint(30, 50),
                'opacity': random.uniform(0.1, 0.3)
            },
            {
                'type': 'cube',
                'color': self._generate_bright_color(),
                'size': random.randint(40, 80),
                'rotation': random.uniform(0, 360),
                'position': (random.randint(100, 500), random.randint(100, 500))
            },
            {
                'type': 'hexagon',
                'color': self._generate_bright_color(),
                'size': random.randint(30, 60),
                'position': (random.randint(100, 500), random.randint(100, 500))
            }
        ]

    def render(self, display: np.ndarray) -> None:
        for element in self.elements:
            if element['type'] == 'grid':
                self._draw_grid(display, element)
            elif element['type'] == 'cube':
                self._draw_cube(display, element)
            elif element['type'] == 'hexagon':
                self._draw_hexagon(display, element)

    def _draw_grid(self, display: np.ndarray, element: dict):
        h, w = display.shape[:2]
        spacing = element['spacing']
        color = element['color']
        opacity = element['opacity']
        
        overlay = display.copy()
        for x in range(0, w, spacing):
            cv2.line(overlay, (x, 0), (x, h), color, 1, cv2.LINE_AA)
        for y in range(0, h, spacing):
            cv2.line(overlay, (0, y), (w, y), color, 1, cv2.LINE_AA)
            
        cv2.addWeighted(overlay, opacity, display, 1 - opacity, 0, display)

    def _draw_cube(self, display: np.ndarray, element: dict):
        size = element['size']
        color = element['color']
        x, y = element['position']
        
        # Draw cube wireframe
        points = np.array([
            [[-size/2, -size/2, -size/2], [size/2, -size/2, -size/2], 
             [size/2, size/2, -size/2], [-size/2, size/2, -size/2],
             [-size/2, -size/2, size/2], [size/2, -size/2, size/2],
             [size/2, size/2, size/2], [-size/2, size/2, size/2]]
        ], dtype=np.float32)
        
        # Rotation matrix
        angle = element['rotation']
        R = cv2.getRotationMatrix2D((0, 0), angle, 1.0)
        
        # Project and draw
        for i in range(4):
            pt1 = (int(points[0,i,0] + x), int(points[0,i,1] + y))
            pt2 = (int(points[0,(i+1)%4,0] + x), int(points[0,(i+1)%4,1] + y))
            cv2.line(display, pt1, pt2, color, 1, cv2.LINE_AA)

    def _draw_hexagon(self, display: np.ndarray, element: dict):
        size = element['size']
        color = element['color']
        x, y = element['position']
        
        points = []
        for i in range(6):
            angle = i * np.pi / 3
            px = int(x + size * np.cos(angle))
            py = int(y + size * np.sin(angle))
            points.append([px, py])
            
        points = np.array(points, np.int32)
        cv2.polylines(display, [points], True, color, 1, cv2.LINE_AA) 