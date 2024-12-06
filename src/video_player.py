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
        
        # Create a grid to track occupied spaces
        grid_size = 20  # Grid divisions for overlap checking
        occupied_grid = np.zeros((grid_size, grid_size), dtype=bool)
        
        for _ in range(count):
            # Randomly choose between vertical and horizontal orientation
            is_vertical = random.random() > 0.5
            
            if is_vertical:
                aspect_ratio = random.uniform(1.5, 2.5)  # Taller than wide
            else:
                aspect_ratio = random.uniform(0.4, 0.8)  # Wider than tall
            
            base_size = random.uniform(self.min_scale, self.max_scale)
            
            # Calculate dimensions based on orientation
            if is_vertical:
                width = base_size
                height = base_size * aspect_ratio
            else:
                height = base_size
                width = base_size * aspect_ratio
            
            # Calculate actual pixel dimensions
            target_width = int(self.display_width * width)
            target_height = int(self.display_height * height)
            
            # Try to find a position with minimal overlap
            best_position = None
            min_overlap = float('inf')
            
            # Try several random positions and pick the one with least overlap
            for _ in range(10):  # Number of attempts to find good position
                x = random.randint(0, max(0, self.display_width - target_width))
                y = random.randint(0, max(0, self.display_height - target_height))
                
                # Convert position to grid coordinates
                grid_x = int(x * grid_size / self.display_width)
                grid_y = int(y * grid_size / self.display_height)
                grid_w = int(target_width * grid_size / self.display_width)
                grid_h = int(target_height * grid_size / self.display_height)
                
                # Calculate overlap in grid
                overlap = 0
                for gx in range(max(0, grid_x), min(grid_size, grid_x + grid_w)):
                    for gy in range(max(0, grid_y), min(grid_size, grid_y + grid_h)):
                        if occupied_grid[gy, gx]:
                            overlap += 1
                
                if overlap < min_overlap:
                    min_overlap = overlap
                    best_position = (x, y)
            
            # Update occupied grid with chosen position
            grid_x = int(best_position[0] * grid_size / self.display_width)
            grid_y = int(best_position[1] * grid_size / self.display_height)
            grid_w = int(target_width * grid_size / self.display_width)
            grid_h = int(target_height * grid_size / self.display_height)
            
            for gx in range(max(0, grid_x), min(grid_size, grid_x + grid_w)):
                for gy in range(max(0, grid_y), min(grid_size, grid_y + grid_h)):
                    occupied_grid[gy, gx] = True
            
            # Create container with varied orientation and better positioning
            container = {
                'width_scale': width,
                'height_scale': height,
                'position': best_position,
                'cutout_size': random.uniform(self.cutout_min_size, self.cutout_max_size),
                'cutout_x': random.random(),
                'cutout_y': random.random(),
                'is_vertical': is_vertical
            }
            containers.append(container)
        
        return containers

    def apply_container_transform(self, frame: np.ndarray, container: dict) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Apply fixed container settings to frame"""
        height, width = frame.shape[:2]
        
        # Use fixed dimensions
        target_width = int(self.display_width * container['width_scale'])
        target_height = int(self.display_height * container['height_scale'])
        
        # Apply fixed cutout with orientation consideration
        crop_size = int(min(width, height) * container['cutout_size'])
        if container['is_vertical']:
            crop_width = crop_size
            crop_height = int(crop_size * 1.5)  # Make vertical crops taller
        else:
            crop_width = int(crop_size * 1.5)  # Make horizontal crops wider
            crop_height = crop_size
        
        # Ensure crop dimensions don't exceed frame
        crop_width = min(crop_width, width)
        crop_height = min(crop_height, height)
        
        # Calculate crop position
        start_x = int((width - crop_width) * container['cutout_x'])
        start_y = int((height - crop_height) * container['cutout_y'])
        
        # Apply crop
        frame = frame[start_y:start_y+crop_height, start_x:start_x+crop_width]
        
        # Calculate scaling factors for both dimensions
        scale_x = target_width / frame.shape[1]
        scale_y = target_height / frame.shape[0]
        
        # Use the larger scaling factor to ensure the frame fills the container
        scale = max(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(frame.shape[1] * scale)
        new_height = int(frame.shape[0] * scale)
        
        # Resize frame
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Center crop to target size
        start_x = (new_width - target_width) // 2
        start_y = (new_height - target_height) // 2
        
        frame = frame[start_y:start_y+target_height, start_x:start_x+target_width]
        
        return frame, (target_width, target_height)

    def run(self):
        """Main video playback loop"""
        if not self.videos:
            print("No videos found in the specified folder")
            return
            
        display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
        cv2.namedWindow('Video Display', cv2.WINDOW_NORMAL)
        
        while True:
            if self.cap is None or not self.cap.isOpened():
                try:
                    # Load new video and generate new container settings
                    self.current_video = random.choice(self.videos)
                    print(f"Playing: {self.current_video}")
                    video_path = os.path.join(self.folder_path, self.current_video)
                    
                    if not os.path.exists(video_path):
                        print(f"Error: Video file not found: {video_path}")
                        continue
                    
                    self.cap = cv2.VideoCapture(video_path)
                    if not self.cap.isOpened():
                        print(f"Error: Could not open video: {video_path}")
                        continue
                    
                    self.objects = self.generate_container_settings()
                except Exception as e:
                    print(f"Error loading video: {str(e)}")
                    if self.cap is not None:
                        self.cap.release()
                    self.cap = None
                    continue
            
            # Clear display
            display.fill(0)
            
            # Read frame
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print(f"End of video or error reading frame: {self.current_video}")
                    self.cap.release()
                    self.cap = None
                    continue
                
                # Draw each container
                for i, container in enumerate(self.objects):
                    try:
                        container_frame, (w, h) = self.apply_container_transform(frame.copy(), container)
                        x, y = container['position']
                        
                        # Add text above container
                        text_y = max(y - 15, 0)  # Position text 15 pixels above container
                        text = f"Vid: {self.current_video[:20]} | Pos: ({x},{y}) | Scale: {container['width_scale']:.2f}x{container['height_scale']:.2f}"
                        cv2.putText(display, text, (x, text_y), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                        
                        # Draw container frame
                        display[y:y+h, x:x+w] = container_frame
                    except Exception as e:
                        print(f"Error processing container: {str(e)}")
                        continue
                
                cv2.imshow('Video Display', display)
                
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                if self.cap is not None:
                    self.cap.release()
                self.cap = None
                continue
            
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
