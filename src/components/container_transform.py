import cv2
import numpy as np
from typing import Tuple, Dict, List
import random

class ContainerTransform:
    def __init__(self, display_width: int, display_height: int, 
                 min_objects: int = 4, max_objects: int = 8,
                 min_scale: float = 0.1, max_scale: float = 0.3):
        self.display_width = display_width
        self.display_height = display_height
        self.min_objects = min_objects
        self.max_objects = max_objects
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.cutout_min_size = 0.3
        self.cutout_max_size = 0.7

    def generate_container_settings(self) -> List[dict]:
        """Generate containers with varied shapes and orientations"""
        count = random.randint(self.min_objects, self.max_objects)
        containers = []
        
        # Define container types with weights
        container_types = [
            ('vertical_stripe', 0.4),    # 40% chance for vertical stripes
            ('horizontal_stripe', 0.2),   # 20% chance for horizontal stripes
            ('square', 0.4)              # 40% chance for squares
        ]
        
        while len(containers) < count:
            # Choose container type based on weights
            container_type = random.choices(
                [t[0] for t in container_types],
                weights=[t[1] for t in container_types]
            )[0]
            
            if container_type == 'vertical_stripe':
                width = random.uniform(0.05, 0.15)  # Narrow width
                height = random.uniform(0.3, 1.0)   # Varied height
                is_vertical = True
            elif container_type == 'horizontal_stripe':
                width = random.uniform(0.3, 0.8)    # Wide width
                height = random.uniform(0.05, 0.15)  # Short height
                is_vertical = False
            else:  # square
                size = random.uniform(0.15, 0.3)
                width = height = size
                is_vertical = random.choice([True, False])
            
            # Try to find placement
            max_attempts = 10
            for _ in range(max_attempts):
                x = random.randint(0, int(self.display_width * (1 - width)))
                y = random.randint(0, int(self.display_height * (1 - height)))
                
                # Check overlap with existing containers
                overlap = False
                for existing in containers:
                    ex, ey = existing['position']
                    ew = self.display_width * existing['width_scale']
                    eh = self.display_height * existing['height_scale']
                    
                    if (x < ex + ew and x + width * self.display_width > ex and
                        y < ey + eh and y + height * self.display_height > ey):
                        overlap = True
                        break
                
                if not overlap:
                    container = {
                        'width_scale': width,
                        'height_scale': height,
                        'position': (x, y),
                        'cutout_size': random.uniform(self.cutout_min_size, self.cutout_max_size),
                        'cutout_x': random.random(),
                        'cutout_y': random.random(),
                        'is_vertical': is_vertical,
                        'rotation': random.choice([0, 90]) if is_vertical else random.choice([0, 270])
                    }
                    containers.append(container)
                    break
            
        return containers

    def apply_transform(self, frame: np.ndarray, container: Dict) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Apply container transformation to frame"""
        target_width = int(self.display_width * container['width_scale'])
        target_height = int(self.display_height * container['height_scale'])
        
        try:
            # Calculate aspect ratios
            frame_aspect = frame.shape[1] / frame.shape[0]
            target_aspect = target_width / target_height
            
            # Calculate dimensions to fill container while maintaining aspect ratio
            if frame_aspect > target_aspect:
                # Width needs to be cropped
                scale = target_height / frame.shape[0]
                new_height = target_height
                new_width = int(frame.shape[1] * scale)
            else:
                # Height needs to be cropped
                scale = target_width / frame.shape[1]
                new_width = target_width
                new_height = int(frame.shape[0] * scale)
            
            # Resize frame
            frame = cv2.resize(frame, (new_width, new_height))
            
            # Center crop to target dimensions
            start_x = (new_width - target_width) // 2
            start_y = (new_height - target_height) // 2
            frame = frame[start_y:start_y + target_height, start_x:start_x + target_width]
            
            # Ensure frame has exactly the target dimensions
            if frame.shape[:2] != (target_height, target_width):
                frame = cv2.resize(frame, (target_width, target_height))
            
            return frame, (target_width, target_height)
            
        except Exception as e:
            print(f"Error in container transform: {str(e)}")
            # Return black frame of correct size
            return np.zeros((target_height, target_width, 3), dtype=np.uint8), (target_width, target_height) 