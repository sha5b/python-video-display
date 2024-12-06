import cv2
import numpy as np
import os
import random
from typing import List, Tuple
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox

class VideoPlayer:
    def __init__(self, folder_path: str, display_width: int, display_height: int):
        # Display settings
        self.folder_path = folder_path
        self.display_width = display_width
        self.display_height = display_height
        
        # Container settings
        self.min_objects = 2
        self.max_objects = 10
        self.min_scale = 0.3
        self.max_scale = 1.0
        self.min_aspect_ratio = 0.5  # More rectangular
        self.max_aspect_ratio = 2.0  # More square-ish
        self.cutout_min_size = 0.3
        self.cutout_max_size = 0.7
        
        # Initialize video handling
        self.videos = self.load_videos()
        self.current_video = None
        self.cap = None
        self.objects = []

    def load_videos(self) -> List[str]:
        """Load all video files from the specified folder"""
        video_extensions = ('.mp4', '.avi', '.mov')
        return [f for f in os.listdir(self.folder_path) 
                if f.lower().endswith(video_extensions)]

    def generate_container_settings(self) -> List[dict]:
        """Generate new fixed container settings when video changes"""
        count = random.randint(self.min_objects, self.max_objects)
        containers = []
        
        for _ in range(count):
            # Generate fixed settings for this container - these won't change until next video
            aspect_ratio = random.uniform(self.min_aspect_ratio, self.max_aspect_ratio)
            base_size = random.uniform(self.min_scale, self.max_scale)
            
            # Calculate fixed width and height based on aspect ratio
            if random.random() > 0.5:
                width = base_size
                height = base_size / aspect_ratio
            else:
                height = base_size
                width = base_size * aspect_ratio
            
            # Create container with ALL fixed settings including cutout position
            container = {
                'width_scale': width,
                'height_scale': height,
                'position': (random.randint(0, self.display_width),
                           random.randint(0, self.display_height)),
                'cutout_size': random.uniform(self.cutout_min_size, self.cutout_max_size),
                # Add fixed cutout positions
                'cutout_x': random.random(),  # Store as percentage
                'cutout_y': random.random()   # Store as percentage
            }
            containers.append(container)
        return containers

    def apply_container_transform(self, frame: np.ndarray, container: dict) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Apply fixed container settings to frame"""
        height, width = frame.shape[:2]
        
        # Use fixed dimensions
        target_width = int(self.display_width * container['width_scale'])
        target_height = int(self.display_height * container['height_scale'])
        
        # Apply fixed cutout using stored positions
        crop_size = int(min(width, height) * container['cutout_size'])
        start_x = int((width - crop_size) * container['cutout_x'])
        start_y = int((height - crop_size) * container['cutout_y'])
        frame = frame[start_y:start_y+crop_size, start_x:start_x+crop_size]
        
        # Scale to fit container while maintaining aspect ratio
        frame_ratio = frame.shape[1] / frame.shape[0]
        container_ratio = target_width / target_height
        
        if frame_ratio > container_ratio:
            new_height = target_height
            new_width = int(new_height * frame_ratio)
        else:
            new_width = target_width
            new_height = int(new_width / frame_ratio)
        
        frame = cv2.resize(frame, (new_width, new_height))
        
        # Center in container
        container_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        y_offset = (target_height - new_height) // 2
        x_offset = (target_width - new_width) // 2
        
        if y_offset < 0:
            frame = frame[-y_offset:target_height-y_offset, :]
            y_offset = 0
        if x_offset < 0:
            frame = frame[:, -x_offset:target_width-x_offset]
            x_offset = 0
        
        try:
            container_frame[y_offset:y_offset+frame.shape[0], 
                           x_offset:x_offset+frame.shape[1]] = frame
        except ValueError:
            container_frame = cv2.resize(frame, (target_width, target_height))
        
        return container_frame, (target_width, target_height)

    def run(self):
        """Main video playback loop"""
        if not self.videos:
            print("No videos found in the specified folder")
            return
            
        display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
        cv2.namedWindow('Video Display', cv2.WINDOW_NORMAL)
        
        while True:
            if self.cap is None or not self.cap.isOpened():
                # Load new video and generate new container settings
                self.current_video = random.choice(self.videos)
                print(f"Playing: {self.current_video}")
                self.cap = cv2.VideoCapture(os.path.join(self.folder_path, self.current_video))
                self.objects = self.generate_container_settings()
            
            # Clear display
            display.fill(0)
            
            # Read frame
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                continue
            
            # Draw each container
            for i, container in enumerate(self.objects):
                container_frame, (w, h) = self.apply_container_transform(frame.copy(), container)
                x, y = container['position']
                
                # Ensure container stays within display bounds
                x = max(0, min(x, self.display_width - w))
                y = max(0, min(y, self.display_height - h))
                
                try:
                    display[int(y):int(y+h), int(x):int(x+w)] = container_frame
                except:
                    continue
            
            cv2.imshow('Video Display', display)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()

class VideoPlayerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Player Setup")
        
        # Variables
        self.folder_path = tk.StringVar()
        self.width = tk.StringVar(value="1280")
        self.height = tk.StringVar(value="720")
        self.min_objects = tk.StringVar(value="2")
        self.max_objects = tk.StringVar(value="10")
        self.min_scale = tk.StringVar(value="0.3")
        self.max_scale = tk.StringVar(value="1.0")
        self.min_aspect_ratio = tk.StringVar(value="0.5")
        self.max_aspect_ratio = tk.StringVar(value="2.0")
        self.cutout_min_size = tk.StringVar(value="0.3")
        self.cutout_max_size = tk.StringVar(value="0.7")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Folder selection
        ttk.Label(main_frame, text="Video Folder:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.folder_path, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Container Settings", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Add settings
        row = 0
        self.add_setting(settings_frame, "Display Width:", self.width, row); row += 1
        self.add_setting(settings_frame, "Display Height:", self.height, row); row += 1
        self.add_setting(settings_frame, "Min Objects:", self.min_objects, row); row += 1
        self.add_setting(settings_frame, "Max Objects:", self.max_objects, row); row += 1
        self.add_setting(settings_frame, "Min Scale:", self.min_scale, row); row += 1
        self.add_setting(settings_frame, "Max Scale:", self.max_scale, row); row += 1
        self.add_setting(settings_frame, "Min Aspect Ratio:", self.min_aspect_ratio, row); row += 1
        self.add_setting(settings_frame, "Max Aspect Ratio:", self.max_aspect_ratio, row); row += 1
        self.add_setting(settings_frame, "Min Cutout Size:", self.cutout_min_size, row); row += 1
        self.add_setting(settings_frame, "Max Cutout Size:", self.cutout_max_size, row)
        
        # Start button
        ttk.Button(main_frame, text="Start Video Player", command=self.start_player).grid(row=2, column=0, columnspan=3, pady=20)
        
    def add_setting(self, parent, label, variable, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(parent, textvariable=variable, width=10).grid(row=row, column=1, padx=5)
        
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            
    def validate_inputs(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a video folder")
            return False
        return True
            
    def start_player(self):
        if not self.validate_inputs():
            return
            
        self.root.destroy()
        
        player = VideoPlayer(
            folder_path=self.folder_path.get(),
            display_width=int(self.width.get()),
            display_height=int(self.height.get())
        )
        
        # Set custom parameters
        player.min_objects = int(self.min_objects.get())
        player.max_objects = int(self.max_objects.get())
        player.min_scale = float(self.min_scale.get())
        player.max_scale = float(self.max_scale.get())
        player.min_aspect_ratio = float(self.min_aspect_ratio.get())
        player.max_aspect_ratio = float(self.max_aspect_ratio.get())
        player.cutout_min_size = float(self.cutout_min_size.get())
        player.cutout_max_size = float(self.cutout_max_size.get())
        
        player.run()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = VideoPlayerGUI()
    gui.run()
