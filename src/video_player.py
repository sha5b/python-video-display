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
        max_attempts = 50  # Maximum attempts to place all containers
        
        # Create a grid to track occupied spaces
        grid_size = 20  # Grid divisions for overlap checking
        occupied_grid = np.zeros((grid_size, grid_size), dtype=bool)
        
        attempt_count = 0
        while len(containers) < count and attempt_count < max_attempts:
            attempt_count += 1
            
            # Force simpler placement for first container if we're struggling
            if len(containers) == 0 and attempt_count > 25:
                # Simplified settings for guaranteed placement
                container = {
                    'width_scale': 0.3,  # Small, conservative size
                    'height_scale': 0.3,
                    'position': (0, 0),  # Top-left corner
                    'cutout_size': 0.5,  # Middle value
                    'cutout_x': 0.5,
                    'cutout_y': 0.5,
                    'is_vertical': False,
                    'rotation': 0
                }
                containers.append(container)
                # Mark position as occupied
                grid_x = 0
                grid_y = 0
                grid_w = max(1, int(0.3 * grid_size))
                grid_h = max(1, int(0.3 * grid_size))
                for gx in range(grid_w):
                    for gy in range(grid_h):
                        occupied_grid[gy, gx] = True
                continue
            
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
            
            if target_width == 0 or target_height == 0:
                continue  # Skip if dimensions are invalid
            
            # Try to find a position with no overlap
            best_position = None
            for _ in range(100):  # Attempts for this specific container
                x = random.randint(0, max(0, self.display_width - target_width))
                y = random.randint(0, max(0, self.display_height - target_height))
                
                # Convert position to grid coordinates
                grid_x = int(x * grid_size / self.display_width)
                grid_y = int(y * grid_size / self.display_height)
                grid_w = max(1, int(target_width * grid_size / self.display_width))
                grid_h = max(1, int(target_height * grid_size / self.display_height))
                
                # Check for overlap in grid
                overlap = False
                for gx in range(max(0, grid_x), min(grid_size, grid_x + grid_w)):
                    for gy in range(max(0, grid_y), min(grid_size, grid_y + grid_h)):
                        if occupied_grid[gy, gx]:
                            overlap = True
                            break
                    if overlap:
                        break
                
                if not overlap:
                    best_position = (x, y)
                    break
            
            if best_position is None:
                print(f"Warning: Could not place container after {attempt_count} attempts")
                continue
            
            # Update occupied grid with chosen position
            grid_x = int(best_position[0] * grid_size / self.display_width)
            grid_y = int(best_position[1] * grid_size / self.display_height)
            grid_w = max(1, int(target_width * grid_size / self.display_width))
            grid_h = max(1, int(target_height * grid_size / self.display_height))
            
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
                'is_vertical': is_vertical,
                'rotation': random.choice([0, 90, 180, 270])
            }
            containers.append(container)
        
        if len(containers) < count:
            print(f"Warning: Could only place {len(containers)} containers out of {count} requested")
        
        return containers

    def apply_container_transform(self, frame: np.ndarray, container: dict) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Apply fixed container settings to frame"""
        height, width = frame.shape[:2]
        
        # Use fixed dimensions
        target_width = int(self.display_width * container['width_scale'])
        target_height = int(self.display_height * container['height_scale'])
        
        # Ensure minimum dimensions
        target_width = max(1, target_width)
        target_height = max(1, target_height)
        
        try:
            # Apply rotation first if needed (using ROTATE_BOUND for better quality)
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
                # Frame is wider than container
                new_height = target_height
                new_width = int(target_height * frame_aspect)
            else:
                # Frame is taller than container
                new_width = target_width
                new_height = int(target_width / frame_aspect)
            
            # Only resize once, using AREA interpolation for downscaling and LINEAR for upscaling
            if new_width < width or new_height < height:
                interpolation = cv2.INTER_AREA  # Better quality for downscaling
            else:
                interpolation = cv2.INTER_LINEAR  # Faster for upscaling
            
            frame = cv2.resize(frame, (new_width, new_height), interpolation=interpolation)
            
            # Calculate crop to center the frame
            start_x = (new_width - target_width) // 2
            start_y = (new_height - target_height) // 2
            
            # Crop to target size
            frame = frame[start_y:start_y+target_height, start_x:start_x+target_width]
            
            # Apply cutout if specified (simplified for performance)
            if container.get('cutout_size', 0) > 0:
                crop_width = int(target_width * container['cutout_size'])
                crop_height = int(target_height * container['cutout_size'])
                
                # Calculate crop position
                start_x = int((target_width - crop_width) * container['cutout_x'])
                start_y = int((target_height - crop_height) * container['cutout_y'])
                
                # Ensure bounds
                start_x = min(max(0, start_x), target_width - crop_width)
                start_y = min(max(0, start_y), target_height - crop_height)
                
                # Single resize operation after crop
                frame = cv2.resize(
                    frame[start_y:start_y+crop_height, start_x:start_x+crop_width],
                    (target_width, target_height),
                    interpolation=cv2.INTER_LINEAR
                )
            
            return frame, (target_width, target_height)
            
        except Exception as e:
            print(f"Error in container transform: {str(e)}")
            return np.zeros((target_height, target_width, 3), dtype=np.uint8), (target_width, target_height)

    def run(self):
        """Main video playback loop"""
        try:
            if not self.videos:
                print("No videos found in the specified folder")
                return
            
            # Pre-allocate display buffer
            display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
            cv2.namedWindow('Video Display', cv2.WINDOW_NORMAL)
            
            # Buffer for frame reading
            ret, frame = True, None
            
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
                        
                        # Set video capture buffer size
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # Get optimal frame delay
                        fps = self.cap.get(cv2.CAP_PROP_FPS)
                        frame_delay = max(1, int(1000 / (fps if fps > 0 else 30)))
                        
                    except Exception as e:
                        print(f"Error loading video: {str(e)}")
                        if self.cap is not None:
                            self.cap.release()
                        self.cap = None
                        continue
                
                # Clear display using numpy operation
                display.fill(0)
                
                # Read frame
                if frame is None:
                    ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    print(f"End of video or error reading frame: {self.current_video}")
                    self.cap.release()
                    self.cap = None
                    continue
                
                # Process containers
                for container in self.objects:
                    try:
                        container_frame, (w, h) = self.apply_container_transform(frame.copy(), container)
                        x, y = container['position']
                        display[y:y+h, x:x+w] = container_frame
                    except Exception as e:
                        print(f"Error processing container: {str(e)}")
                        continue
                
                cv2.imshow('Video Display', display)
                
                # Read next frame while displaying current one
                ret, frame = self.cap.read()
                
                if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
                    break
            
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
        except KeyboardInterrupt:
            print("\nExiting video player...")
        finally:
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
