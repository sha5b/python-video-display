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
        """Generate containers with varied shapes and orientations."""
        count = random.randint(self.min_objects, self.max_objects)
        containers = []

        # Define container types with weights
        container_types = [
            ('vertical_stripe', 0.2),    # 40% chance for vertical stripes
            ('horizontal_stripe', 0.2), # 20% chance for horizontal stripes
            ('square', 0.4)             # 40% chance for squares
        ]

        total_attempts = 0
        max_total_attempts = count * 10  # Allow 10 attempts per container on average

        while len(containers) < count and total_attempts < max_total_attempts:
            total_attempts += 1

            # Choose container type based on weights
            container_type = random.choices(
                [t[0] for t in container_types],
                weights=[t[1] for t in container_types]
            )[0]
            
            # Calculate dimensions based on type
            if container_type == 'vertical_stripe':
                width = random.uniform(0.15, 0.25)
                height = random.uniform(0.4, 1.0)
                is_vertical = True
            elif container_type == 'horizontal_stripe':
                width = random.uniform(0.4, 0.8)
                height = random.uniform(0.15, 0.25)
                is_vertical = False
            else:  # square
                size = random.uniform(0.2, 0.3)
                width = height = size
                is_vertical = random.choice([True, False])

            # Try to find a valid placement
            for _ in range(10):  # Allow up to 10 attempts per container
                x = random.randint(0, int(self.display_width * (1 - width)))
                y = random.randint(0, int(self.display_height * (1 - height)))

                # Check for overlap with existing containers
                if not self._check_overlap(x, y, width, height, containers):
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

        if len(containers) < count:
            print(f"Warning: Only placed {len(containers)} out of {count} requested containers.")
        
        return containers

    def _check_overlap(self, x: int, y: int, width: float, height: float, containers: List[dict]) -> bool:
        """Check if the proposed container overlaps with existing ones."""
        for existing in containers:
            ex, ey = existing['position']
            ew = self.display_width * existing['width_scale']
            eh = self.display_height * existing['height_scale']
            
            if (x < ex + ew and x + width * self.display_width > ex and
                y < ey + eh and y + height * self.display_height > ey):
                return True
        return False

    def apply_transform(self, frame: np.ndarray, container: Dict) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Apply container transformation to frame."""
        target_width = int(self.display_width * container['width_scale'])
        target_height = int(self.display_height * container['height_scale'])

        try:
            # Validate input frame dimensions
            if frame is None or frame.size == 0:
                raise ValueError("Invalid frame provided to apply_transform.")

            # Calculate aspect ratios
            frame_aspect = frame.shape[1] / frame.shape[0]
            target_aspect = target_width / target_height
            
            # Resize while maintaining aspect ratio
            if frame_aspect > target_aspect:
                # Width is the limiting factor
                scale = target_height / frame.shape[0]
                new_width = int(frame.shape[1] * scale)
                new_height = target_height
            else:
                # Height is the limiting factor
                scale = target_width / frame.shape[1]
                new_width = target_width
                new_height = int(frame.shape[0] * scale)

            # Resize frame
            resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # Center crop to target size
            x_start = max(0, (new_width - target_width) // 2)
            y_start = max(0, (new_height - target_height) // 2)
            cropped_frame = resized_frame[y_start:y_start + target_height, x_start:x_start + target_width]

            # Ensure the output frame matches the target size
            if cropped_frame.shape[:2] != (target_height, target_width):
                cropped_frame = cv2.resize(cropped_frame, (target_width, target_height))

            return cropped_frame, (target_width, target_height)

        except Exception as e:
            print(f"Error in container transform: {e}")
            # Return black frame of the correct size on failure
            return np.zeros((target_height, target_width, 3), dtype=np.uint8), (target_width, target_height)
