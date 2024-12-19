import cv2
import numpy as np
import os
import random
from typing import List
import platform

# Configure OpenCV to use GStreamer pipeline for hardware acceleration on Raspberry Pi
def configure_video_backend():
    if platform.machine().startswith('arm'):  # Check if running on Raspberry Pi
        # Use V4L2 backend with hardware acceleration
        os.environ["OPENCV_VIDEOIO_PRIORITY_V4L2"] = "1"
        os.environ["OPENCV_VIDEOIO_PRIORITY_MMAL"] = "1"
        return True
    return False

from components.text_overlay import TextOverlay
from components.container_transform import ContainerTransform
from components.ui_manager import UIManager

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

        # Always use detected system resolution, ignore settings file resolution
        self.display_width = self.system_width
        self.display_height = self.system_height
        
        # Apply other settings but keep detected resolution
        settings['display_width'] = self.display_width
        settings['display_height'] = self.display_height
        self.apply_settings(settings)

    def detect_system_resolution(self) -> tuple[int, int]:
        """Detect the system's current screen resolution."""
        if platform.machine().startswith('arm'):  # Raspberry Pi
            try:
                # Try to get resolution from vcgencmd
                import subprocess
                output = subprocess.check_output(['vcgencmd', 'get_lcd_info'], universal_newlines=True)
                width, height = map(int, output.strip().split(' ')[1].split('x'))
                return width, height
            except Exception as e:
                print(f"Failed to get resolution from vcgencmd: {e}")
                # Fallback to default Raspberry Pi resolution
                return 1920, 1080
        else:
            # For non-Raspberry Pi systems, use OpenCV window detection
            cv2.namedWindow('temp_window', cv2.WINDOW_NORMAL)
            cv2.moveWindow('temp_window', 0, 0)
            cv2.setWindowProperty('temp_window', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.waitKey(100)
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

            # Use GStreamer pipeline for hardware-accelerated decoding on Raspberry Pi
            if platform.machine().startswith('arm'):
                gst_pipeline = (
                    f"filesrc location={video_path} ! "
                    "decodebin ! "
                    "videoconvert ! "
                    "videoscale ! "
                    f"video/x-raw,width={self.display_width},height={self.display_height} ! "
                    "appsink"
                )
                self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            else:
                self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                print(f"Failed to open video: {video_path}")
                return False

            # Optimize capture settings
            if not platform.machine().startswith('arm'):  # Skip if using GStreamer pipeline
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer size
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.display_width)
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
            # Configure video backend for Raspberry Pi
            configure_video_backend()
            
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

                # Get current window dimensions
                window_width = self.display_width
                window_height = self.display_height

                # Calculate scaling to cover entire window while maintaining aspect ratio
                frame_aspect = frame.shape[1] / frame.shape[0]
                window_aspect = window_width / window_height

                if frame_aspect > window_aspect:
                    # Frame is wider - scale to fit height and crop width
                    frame_height = window_height
                    frame_width = int(window_height * frame_aspect)
                    frame = cv2.resize(frame, (frame_width, frame_height))
                    # Crop the width to fill window
                    start_x = (frame_width - window_width) // 2
                    frame = frame[:, start_x:start_x + window_width]
                else:
                    # Frame is taller - scale to fit width and crop height
                    frame_width = window_width
                    frame_height = int(window_width / frame_aspect)
                    frame = cv2.resize(frame, (frame_width, frame_height))
                    # Crop the height to fill window
                    start_y = (frame_height - window_height) // 2
                    frame = frame[start_y:start_y + window_height]

                # Set the frame directly as the display
                display = frame.copy()

                # Dim the background video
                display = cv2.multiply(display, 0.6).astype(np.uint8)

                # Process containers and overlay them on top of the video
                for container in self.objects:
                    try:
                        # Transform and position container
                        container_frame, (w, h) = self.container_transform.apply_transform(frame, container)
                        base_x, base_y = container['position']
                        
                        # Use base position directly since frame fills entire window
                        x = base_x
                        y = base_y
                        
                        # Add text overlay for this container
                        self.text_overlay.render(display, "", (x, y))
                        
                        # Ensure container stays within display bounds
                        y_end = min(y + h, window_height)
                        x_end = min(x + w, window_width)
                        
                        # Only draw container if it's within display bounds
                        if y < window_height and x < window_width and y >= 0 and x >= 0:
                            # Calculate source region based on clipping
                            src_y = 0 if y >= 0 else -y
                            src_x = 0 if x >= 0 else -x
                            src_h = min(container_frame.shape[0] - src_y, y_end - max(y, 0))
                            src_w = min(container_frame.shape[1] - src_x, x_end - max(x, 0))
                            
                            if src_h > 0 and src_w > 0:
                                display[max(y, 0):y_end, max(x, 0):x_end] = \
                                    container_frame[src_y:src_y+src_h, src_x:src_x+src_w]

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
