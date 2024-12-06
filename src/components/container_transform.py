import cv2
import numpy as np
from typing import Tuple, Dict, List
import random

class ContainerTransform:
    def __init__(self, display_width: int, display_height: int, 
                 min_objects: int = 2, max_objects: int = 10,
                 min_scale: float = 0.3, max_scale: float = 1.0):
        self.display_width = display_width
        self.display_height = display_height
        # Container settings
        self.min_objects = min_objects
        self.max_objects = max_objects
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.min_aspect_ratio = 0.5
        self.max_aspect_ratio = 2.0
        self.cutout_min_size = 0.3
        self.cutout_max_size = 0.7
        
        # Grid settings for efficient placement
        self.grid_cols = 4
        self.grid_rows = 3
        self.cell_width = display_width // self.grid_cols
        self.cell_height = display_height // self.grid_rows
        
    def check_overlap(self, new_rect: Tuple[int, int, int, int], 
                     existing_containers: List[Dict]) -> bool:
        """Check if new rectangle overlaps with existing containers"""
        new_x, new_y, new_w, new_h = new_rect
        for container in existing_containers:
            x, y = container['position']
            w = int(self.display_width * container['width_scale'])
            h = int(self.display_height * container['height_scale'])
            
            # Check for overlap
            if (new_x < x + w and new_x + new_w > x and
                new_y < y + h and new_y + new_h > y):
                return True
        return False
    
    def find_placement(self, width: int, height: int, 
                      containers: List[Dict]) -> Tuple[int, int]:
        """Find a suitable placement for a new container"""
        # Try each grid cell
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = col * self.cell_width
                y = row * self.cell_height
                
                # Adjust position to stay within display bounds
                x = min(x, self.display_width - width)
                y = min(y, self.display_height - height)
                
                if not self.check_overlap((x, y, width, height), containers):
                    return x, y
                    
        return None

    def generate_container_settings(self) -> List[dict]:
        """Generate new fixed container settings when video changes"""
        count = random.randint(self.min_objects, self.max_objects)
        containers = []
        scale_factor = 1.0
        
        while len(containers) < count and scale_factor >= 0.5:
            # Calculate target size based on current scale factor
            base_size = random.uniform(
                self.min_scale * scale_factor, 
                self.max_scale * scale_factor
            )
            
            # More varied aspect ratios
            is_vertical = random.random() > 0.5
            if is_vertical:
                aspect_ratio = random.uniform(0.8, 2.5)  # More extreme vertical variations
            else:
                aspect_ratio = random.uniform(0.4, 1.25)  # More extreme horizontal variations
            
            # Calculate dimensions
            width = base_size * (1/aspect_ratio if is_vertical else aspect_ratio)
            height = base_size * (aspect_ratio if is_vertical else 1/aspect_ratio)
            
            target_width = int(self.display_width * width)
            target_height = int(self.display_height * height)
            
            if target_width == 0 or target_height == 0:
                continue
                
            # Try to find placement
            position = self.find_placement(target_width, target_height, containers)
            
            if position:
                # Successfully placed container
                x, y = position
                container = {
                    'width_scale': width,
                    'height_scale': height,
                    'position': (x, y),
                    'cutout_size': random.uniform(self.cutout_min_size, self.cutout_max_size),
                    'cutout_x': random.random(),
                    'cutout_y': random.random(),
                    'is_vertical': is_vertical,
                    'rotation': random.choice([0, 90, 180, 270])
                }
                containers.append(container)
            else:
                # If placement failed, reduce scale for next attempts
                scale_factor *= 0.9
        
        return containers

    def apply_transform(self, frame: np.ndarray, container: Dict) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Apply container transformation to frame"""
        target_width = int(self.display_width * container['width_scale'])
        target_height = int(self.display_height * container['height_scale'])
        
        try:
            # Apply rotation first if needed
            if container['rotation'] != 0:
                frame = cv2.rotate(frame, {
                    90: cv2.ROTATE_90_CLOCKWISE,
                    180: cv2.ROTATE_180,
                    270: cv2.ROTATE_90_COUNTERCLOCKWISE
                }[container['rotation']])
            
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