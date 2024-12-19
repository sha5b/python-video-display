import cv2
import numpy as np
from typing import Tuple, Dict, List
import random

class ContainerTransform:
    def __init__(self, display_width: int, display_height: int, 
                 min_objects: int = 3, max_objects: int = 6,
                 min_scale: float = 0.15, max_scale: float = 0.4):
        self.display_width = display_width
        self.display_height = display_height
        self.min_objects = min_objects
        self.max_objects = max_objects
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.cutout_min_size = 0.2  # Allow smaller cutouts
        self.cutout_max_size = 0.8  # Allow larger cutouts
        
        # Grid system setup with dynamic spacing
        self.grid_cols = 12  # Divide screen into 12 columns
        self.grid_rows = 8   # and 8 rows
        self.spacing = int(min(display_width, display_height) * 0.02)  # Dynamic spacing based on screen size
        self.cell_width = (self.display_width - (self.grid_cols + 1) * self.spacing) / self.grid_cols
        self.cell_height = (self.display_height - (self.grid_rows + 1) * self.spacing) / self.grid_rows
        self.grid = [[False for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]

    def _find_grid_space(self, width_cells: int, height_cells: int) -> Tuple[int, int]:
        """Find available space in the grid for a container of given size."""
        # Get all available positions
        available_positions = []
        for row in range(self.grid_rows - height_cells + 1):
            for col in range(self.grid_cols - width_cells + 1):
                if self._is_space_available(row, col, width_cells, height_cells):
                    available_positions.append((row, col))
        
        # Return random position if available, otherwise -1, -1
        if available_positions:
            return random.choice(available_positions)
        return -1, -1

    def _is_space_available(self, start_row: int, start_col: int, width_cells: int, height_cells: int) -> bool:
        """Check if the specified grid space is available."""
        for row in range(start_row, start_row + height_cells):
            for col in range(start_col, start_col + width_cells):
                if row >= self.grid_rows or col >= self.grid_cols or self.grid[row][col]:
                    return False
        return True

    def _occupy_grid_space(self, start_row: int, start_col: int, width_cells: int, height_cells: int):
        """Mark grid cells as occupied."""
        for row in range(start_row, start_row + height_cells):
            for col in range(start_col, start_col + width_cells):
                self.grid[row][col] = True

    def generate_container_settings(self) -> List[dict]:
        """Generate containers using a grid-based placement system."""
        count = random.randint(self.min_objects, self.max_objects)
        containers = []
        self.grid = [[False for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        
        # Define container types with varied sizes and weights
        container_types = [
            ('vertical_stripe', 0.35),
            ('horizontal_stripe', 0.35),
            ('square', 0.3)
        ]
        
        attempts = count * 3  # Increase attempts for better placement
        placed = 0

        while placed < count and attempts > 0:
            container_type = random.choices(
                [t[0] for t in container_types],
                weights=[t[1] for t in container_types]
            )[0]

            # Define grid cell requirements with more variation
            if container_type == 'vertical_stripe':
                width_cells = random.randint(1, 3)
                height_cells = random.randint(3, 6)  # Allow taller vertical stripes
                is_vertical = True
            elif container_type == 'horizontal_stripe':
                width_cells = random.randint(3, 6)  # Allow wider horizontal stripes
                height_cells = random.randint(1, 3)
                is_vertical = False
            else:  # square
                size = random.randint(2, 4)  # Allow larger squares
                width_cells = height_cells = size
                is_vertical = random.choice([True, False])

            # Add size variation based on position
            if random.random() < 0.3:  # 30% chance for size adjustment
                if container_type == 'vertical_stripe':
                    height_cells = min(8, height_cells + random.randint(1, 2))
                elif container_type == 'horizontal_stripe':
                    width_cells = min(12, width_cells + random.randint(1, 2))

            # Find random space in grid
            row, col = self._find_grid_space(width_cells, height_cells)
            
            if row != -1:  # Space found
                # Calculate dimensions with more dynamic scaling
                base_width_scale = (width_cells * self.cell_width) / self.display_width
                base_height_scale = (height_cells * self.cell_height) / self.display_height
                
                # Add scale variation
                scale_variation = random.uniform(0.9, 1.1)
                width_scale = base_width_scale * scale_variation
                height_scale = base_height_scale * scale_variation
                
                # Add more varied positioning
                x = int(col * (self.cell_width + self.spacing) + self.spacing + 
                       random.uniform(-self.spacing, self.spacing))
                y = int(row * (self.cell_height + self.spacing) + self.spacing + 
                       random.uniform(-self.spacing, self.spacing))
                
                # Ensure containers stay within display bounds
                x = max(self.spacing, min(x, self.display_width - int(width_scale * self.display_width) - self.spacing))
                y = max(self.spacing, min(y, self.display_height - int(height_scale * self.display_height) - self.spacing))

                container = {
                    'width_scale': width_scale,
                    'height_scale': height_scale,
                    'position': (x, y),
                    'cutout_size': random.uniform(self.cutout_min_size, self.cutout_max_size),
                    'cutout_x': random.random(),
                    'cutout_y': random.random(),
                    'is_vertical': is_vertical,
                    'rotation': random.choice([0, 90]) if is_vertical else random.choice([0, 270])
                }
                
                containers.append(container)
                self._occupy_grid_space(row, col, width_cells, height_cells)
                placed += 1
            
            attempts -= 1

        if placed < count:
            print(f"Warning: Only placed {placed} out of {count} requested containers.")
        
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
