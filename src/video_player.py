import cv2
import numpy as np
import os
import random
from typing import List
from components.text_overlay import TextOverlay
from components.container_transform import ContainerTransform
from components.ui_manager import UIManager

class VideoPlayer:
    def __init__(self):
        # Initialize UI manager
        self.ui_manager = UIManager()
        
        # Get last used settings without showing UI
        settings = self.ui_manager.load_settings()
        if not settings:
            # If no settings exist, show UI to get initial settings
            settings = self.ui_manager.get_settings_with_ui()
            if not settings:
                print("Setup cancelled")
                return
                
        self.apply_settings(settings)

    def apply_settings(self, settings):
        """Apply the given settings to the video player"""
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
        """Load all video files from the specified folder"""
        video_extensions = ('.mp4', '.avi', '.mov')
        if not os.path.exists(self.folder_path):
            print(f"Error: Folder not found: {self.folder_path}")
            return []
        videos = [f for f in os.listdir(self.folder_path) 
                if f.lower().endswith(video_extensions)]
        print(f"Found {len(videos)} videos in {self.folder_path}")
        return videos

    def load_next_video(self):
        """Load the next random video"""
        try:
            if self.cap is not None:
                self.cap.release()
                
            self.current_video = random.choice(self.videos)
            print(f"Playing: {self.current_video}")
            video_path = os.path.join(self.folder_path, self.current_video)
            
            if not os.path.exists(video_path):
                print(f"Error: Video file not found: {video_path}")
                return False
            
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                print(f"Error: Could not open video: {video_path}")
                return False
            
            self.objects = self.container_transform.generate_container_settings()
            
            # Set video capture buffer size
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return True
            
        except Exception as e:
            print(f"Error loading video: {str(e)}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            return False

    def run(self):
        """Main video playback loop"""
        try:
            if not self.videos:
                print("No videos found in the selected folder")
                return
            
            # Create display window
            self.ui_manager.create_window()
            display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
            
            # Load first video
            if not self.load_next_video():
                return
                
            ret, frame = self.cap.read()
            
            while True:
                if not ret or frame is None:
                    print(f"End of video or error reading frame: {self.current_video}")
                    if not self.load_next_video():
                        continue
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        continue
                
                display.fill(0)
                
                # Process containers
                for container in self.objects:
                    try:
                        # Apply container transform
                        container_frame, (w, h) = self.container_transform.apply_transform(
                            frame.copy(), container)
                        
                        # Draw container
                        x, y = container['position']
                        display[y:y+h, x:x+w] = container_frame
                        
                        # Draw text overlay
                        text = f"{self.current_video[:20]} | ({x},{y}) | {container['width_scale']:.2f}x{container['height_scale']:.2f}"
                        self.text_overlay.render(display, text, (x, y), 
                                              container['rotation'], 
                                              self.display_width, 
                                              self.display_height)
                        
                    except Exception as e:
                        print(f"Error processing container: {str(e)}")
                        continue
                
                # Update display and check for quit or settings
                key = self.ui_manager.update_display(display)
                if key == 'q':
                    break
                elif key == 's':
                    # Show settings UI
                    new_settings = self.ui_manager.get_settings_with_ui()
                    if new_settings:
                        self.apply_settings(new_settings)
                        display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
                        if not self.load_next_video():
                            continue
                
                # Read next frame while displaying current one
                ret, frame = self.cap.read()
            
        except KeyboardInterrupt:
            print("\nExiting video player...")
        finally:
            if self.cap is not None:
                self.cap.release()
            self.ui_manager.cleanup()

if __name__ == "__main__":
    player = VideoPlayer()
    player.run()
