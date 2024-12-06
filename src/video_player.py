import cv2
import numpy as np
import os
import random
from typing import List
from components.text_overlay import TextOverlay
from components.container_transform import ContainerTransform
from components.ui_manager import UIManager
from components.background_elements import BackgroundElements


class VideoPlayer:
    def __init__(self):
        # Initialize UI manager
        self.ui_manager = UIManager()

        # Automatically detect system resolution
        self.system_width, self.system_height = self.detect_system_resolution()

        # Get last used settings without showing UI
        settings = self.ui_manager.load_settings()
        if not settings:
            # If no settings exist, show UI to get initial settings
            settings = self.ui_manager.get_settings_with_ui()
            if not settings:
                print("Setup cancelled")
                return

        # Ensure settings use the detected system resolution
        settings['display_width'] = self.system_width
        settings['display_height'] = self.system_height
        self.apply_settings(settings)

    def detect_system_resolution(self) -> tuple[int, int]:
        """Detect the system's current screen resolution."""
        screen = cv2.namedWindow('temp_window', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('temp_window', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        screen_width = int(cv2.getWindowImageRect('temp_window')[2])
        screen_height = int(cv2.getWindowImageRect('temp_window')[3])
        cv2.destroyWindow('temp_window')
        return screen_width, screen_height

    def apply_settings(self, settings):
        """Apply the given settings to the video player."""
        # Display settings
        self.display_width = settings['display_width']
        self.display_height = settings['display_height']
        self.folder_path = settings['folder_path']

        # Initialize components
        self.text_overlay = TextOverlay()
        self.container_transform = ContainerTransform(
            self.display_width,
            self.display_height,
            min_objects=settings['min_objects'],
            max_objects=settings['max_objects'],
            min_scale=settings['min_scale'],
            max_scale=settings['max_scale']
        )
        self.background_elements = BackgroundElements()

        # Initialize video handling
        self.videos = self.load_videos()
        self.current_video = None
        self.cap = None
        self.objects = []

    def load_videos(self) -> List[str]:
        """Load all video files from the specified folder."""
        video_extensions = ('.mp4', '.avi', '.mov')
        if not os.path.exists(self.folder_path):
            print(f"Error: Folder not found: {self.folder_path}")
            return []
        videos = [f for f in os.listdir(self.folder_path)
                  if f.lower().endswith(video_extensions)]
        print(f"Found {len(videos)} videos in {self.folder_path}")
        return videos

    def load_next_video(self):
        """Load the next random video."""
        try:
            if self.cap is not None:
                self.cap.release()

            self.current_video = random.choice(self.videos)
            video_path = os.path.join(self.folder_path, self.current_video)

            if not os.path.exists(video_path):
                print(f"Video not found: {video_path}")
                return False

            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                print(f"Failed to open video: {video_path}")
                return False

            # Optimize capture settings for Raspberry Pi or other low-power devices
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer size
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.display_width)  # Set capture size
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.display_height)

            # Get video properties
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0  # Default to 30 FPS if unavailable
            self.frame_time = max(1, int(1000 / self.fps))  # Frame time in milliseconds

            self.objects = self.container_transform.generate_container_settings()
            return True

        except Exception as e:
            print(f"Error loading video: {str(e)}")
            if self.cap is not None:
                self.cap.release()
            return False

    def run(self):
        """Main video playback loop."""
        try:
            if not self.videos:
                print("No videos found in the selected folder")
                return

            # Create display window
            self.ui_manager.create_window()
            cv2.setWindowProperty(self.ui_manager.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)

            # Frame counter for background updates
            frame_count = 0

            # Load first video
            if not self.load_next_video():
                return

            ret, frame = self.cap.read()

            while True:
                if not ret or frame is None:
                    if not self.load_next_video():
                        continue
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        continue

                # Clear display buffer
                display.fill(0)

                # Render background grid
                self.background_elements.render(display, frame_count)

                # Process containers and render text overlays
                for container in self.objects:
                    try:
                        # Transform and render container
                        container_frame, (w, h) = self.container_transform.apply_transform(frame, container)
                        x, y = container['position']
                        display[y:y + h, x:x + w] = container_frame

                        # Render text overlay for the container
                        self.text_overlay.render(
                            display=display,
                            text="",
                            position=(x + w // 2, y - 10),  # Centered above the container
                            rotation=0,
                            display_width=self.display_width,
                            display_height=self.display_height
                        )

                    except Exception as e:
                        print(f"Error processing container: {str(e)}")
                        continue

                # Update display
                key = self.ui_manager.update_display(display, self.frame_time)
                if key == 'q':
                    break
                elif key == 's':
                    new_settings = self.ui_manager.get_settings_with_ui()
                    if new_settings:
                        self.apply_settings(new_settings)
                        display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
                        if not self.load_next_video():
                            continue

                # Read next frame
                ret, frame = self.cap.read()
                frame_count += 1

        except KeyboardInterrupt:
            print("\nExiting video player...")
        finally:
            if self.cap is not None:
                self.cap.release()
            self.ui_manager.cleanup()


if __name__ == "__main__":
    player = VideoPlayer()
    player.run()
