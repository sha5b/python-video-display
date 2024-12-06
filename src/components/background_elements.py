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
        self.last_rendered_frame = None  # Cache the last rendered grid
        self.last_position = None  # Track the last grid position

    def render(self, display: np.ndarray, frame_count: int) -> None:
        """
        Render the background grid onto the display.
        Update the grid every 10 frames to reduce rendering overhead.
        """
        # Only update the grid every 10 frames
        if frame_count % 10 == 0 or self.last_rendered_frame is None:
            self._draw_moving_grid(display)
        else:
            # Reuse the cached frame if no updates are needed
            if self.last_rendered_frame is not None:
                display[:] = cv2.addWeighted(self.last_rendered_frame, self.grid_opacity, display, 1 - self.grid_opacity, 0)

    def _draw_moving_grid(self, display: np.ndarray):
        """
        Draw the moving grid on the display.
        """
        h, w = display.shape[:2]
        spacing = self.grid_spacing
        color = self.grid_color

        # Create a blank overlay for the grid
        overlay = np.zeros_like(display)
        self.grid_position = (self.grid_position + self.grid_speed) % spacing

        # Draw vertical lines
        for x in range(-spacing, w, spacing):
            cv2.line(overlay, (x + self.grid_position, 0), (x + self.grid_position, h), color, 1, cv2.LINE_AA)

        # Draw horizontal lines
        for y in range(-spacing, h, spacing):
            cv2.line(overlay, (0, y + self.grid_position), (w, y + self.grid_position), color, 1, cv2.LINE_AA)

        # Cache the rendered grid
        self.last_rendered_frame = overlay.copy()

        # Blend the overlay with the display
        cv2.addWeighted(overlay, self.grid_opacity, display, 1 - self.grid_opacity, 0, display)
