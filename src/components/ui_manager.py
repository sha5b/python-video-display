import cv2
import tkinter as tk
from tkinter import filedialog, ttk
import os
import json
from typing import Optional, Tuple, Dict
import platform

class UIManager:
    def __init__(self):
        # Initialize Tkinter
        self.root = tk.Tk()
        self.root.title("Video Display Settings")
        self.root.withdraw()  # Hide window initially to avoid blocking
        
        # Settings file path
        self.settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        
        # Load saved settings or use defaults
        saved_settings = self.load_settings()
        
        # On Raspberry Pi, force portrait resolution
        if platform.machine().startswith('arm'):
            default_width = '480'
            default_height = '1920'
        else:
            default_width = '1920'
            default_height = '1080'
        
        # Settings variables with saved or default values
        self.settings = {
            'display_width': tk.StringVar(value=saved_settings.get('display_width', default_width)),
            'display_height': tk.StringVar(value=saved_settings.get('display_height', default_height)),
            'min_objects': tk.StringVar(value=saved_settings.get('min_objects', '2')),
            'max_objects': tk.StringVar(value=saved_settings.get('max_objects', '10')),
            'min_scale': tk.StringVar(value=saved_settings.get('min_scale', '0.3')),
            'max_scale': tk.StringVar(value=saved_settings.get('max_scale', '1.0')),
            'folder_path': tk.StringVar(value=saved_settings.get('folder_path', ''))
        }
        
        # Create UI elements
        self.create_ui_elements()
        
        # Window settings
        self.window_name = 'Video Display'
        
        self.started = False
        self.fullscreen = False  # Track fullscreen state
    
    def load_settings(self) -> Dict:
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Convert values to appropriate types
                    return {
                        'display_width': int(settings.get('display_width', 1920)),
                        'display_height': int(settings.get('display_height', 1080)),
                        'min_objects': int(settings.get('min_objects', 2)),
                        'max_objects': int(settings.get('max_objects', 10)),
                        'min_scale': float(settings.get('min_scale', 0.3)),
                        'max_scale': float(settings.get('max_scale', 1.0)),
                        'folder_path': str(settings.get('folder_path', ''))
                    }
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {
            'display_width': 1920,
            'display_height': 1080,
            'min_objects': 2,
            'max_objects': 10,
            'min_scale': 0.3,
            'max_scale': 1.0,
            'folder_path': ''
        }
        
    def save_settings(self, settings: Dict) -> None:
        """Save settings to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_current_settings(self) -> Dict:
        """Get current settings without showing UI."""
        try:
            return {
                'display_width': int(self.settings['display_width'].get()),
                'display_height': int(self.settings['display_height'].get()),
                'min_objects': int(self.settings['min_objects'].get()),
                'max_objects': int(self.settings['max_objects'].get()),
                'min_scale': float(self.settings['min_scale'].get()),
                'max_scale': float(self.settings['max_scale'].get()),
                'folder_path': self.settings['folder_path'].get()
            }
        except (ValueError, TypeError) as e:
            print(f"Error parsing settings: {e}")
            return None
    
    def get_settings_with_ui(self) -> Optional[Dict]:
        """Show UI and get settings."""
        self.root.deiconify()  # Show window
        self.root.mainloop()  # Start the Tkinter loop
        if self.started:
            settings = self.get_current_settings()
            if settings:
                self.save_settings(settings)
            return settings
        return None
    
    def create_ui_elements(self):
        """Create all UI elements."""
        # Create and pack the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Display settings
        ttk.Label(self.main_frame, text="Display Settings").grid(row=0, column=0, columnspan=2, pady=5)
        ttk.Label(self.main_frame, text="Width:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(self.main_frame, textvariable=self.settings['display_width']).grid(row=1, column=1, padx=5)
        ttk.Label(self.main_frame, text="Height:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(self.main_frame, textvariable=self.settings['display_height']).grid(row=2, column=1, padx=5)
        
        # Container settings
        ttk.Label(self.main_frame, text="\nContainer Settings").grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Label(self.main_frame, text="Min Objects:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(self.main_frame, textvariable=self.settings['min_objects']).grid(row=4, column=1, padx=5)
        ttk.Label(self.main_frame, text="Max Objects:").grid(row=5, column=0, sticky=tk.W)
        ttk.Entry(self.main_frame, textvariable=self.settings['max_objects']).grid(row=5, column=1, padx=5)
        ttk.Label(self.main_frame, text="Min Scale:").grid(row=6, column=0, sticky=tk.W)
        ttk.Entry(self.main_frame, textvariable=self.settings['min_scale']).grid(row=6, column=1, padx=5)
        ttk.Label(self.main_frame, text="Max Scale:").grid(row=7, column=0, sticky=tk.W)
        ttk.Entry(self.main_frame, textvariable=self.settings['max_scale']).grid(row=7, column=1, padx=5)
        
        # Folder selection
        ttk.Label(self.main_frame, text="\nVideo Folder").grid(row=8, column=0, columnspan=2, pady=5)
        ttk.Entry(self.main_frame, textvariable=self.settings['folder_path']).grid(row=9, column=0, padx=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_folder).grid(row=9, column=1, padx=5)
        
        # Start button
        ttk.Button(self.main_frame, text="Start", command=self.start).grid(row=10, column=0, columnspan=2, pady=20)
        
        # Fullscreen toggle button
        ttk.Button(self.main_frame, text="Toggle Fullscreen", command=self.toggle_fullscreen).grid(row=11, column=0, columnspan=2, pady=10)
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.started = False
    
    def browse_folder(self):
        """Open folder selection dialog."""
        initial_dir = self.settings['folder_path'].get() or os.path.expanduser('~')
        folder_path = filedialog.askdirectory(
            title='Select Video Folder',
            initialdir=initial_dir
        )
        if folder_path:
            self.settings['folder_path'].set(folder_path)
    
    def start(self):
        """Start button callback."""
        self.started = True
        self.root.withdraw()  # Hide window instead of quitting
        self.root.quit()
    
    def create_window(self) -> None:
        """Create and configure the OpenCV window."""
        if platform.machine().startswith('arm'):  # Raspberry Pi
            # Create window with normal mode first
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.moveWindow(self.window_name, 0, 0)
            
            # Wait for window to be fully created and visible
            cv2.waitKey(500)  # Increased wait time for window creation
            
            # Now set fullscreen property
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.waitKey(100)  # Wait for fullscreen to take effect
            
            # Get actual system resolution
            screen_rect = cv2.getWindowImageRect(self.window_name)
            if screen_rect is not None:
                actual_width = screen_rect[2]
                actual_height = screen_rect[3]
                print(f"Detected system resolution: {actual_width}x{actual_height}")
                
                # Update settings with actual resolution while maintaining portrait orientation
                if actual_width > actual_height:
                    # Landscape screen - rotate for portrait
                    self.settings['display_width'].set(str(min(actual_width, actual_height)))
                    self.settings['display_height'].set(str(max(actual_width, actual_height)))
                else:
                    # Already portrait
                    self.settings['display_width'].set(str(actual_width))
                    self.settings['display_height'].set(str(actual_height))
            
            # Recreate window with correct settings
            cv2.destroyWindow(self.window_name)
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.moveWindow(self.window_name, 0, 0)
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            self.fullscreen = True
            
            width = int(self.settings['display_width'].get())
            height = int(self.settings['display_height'].get())
            print(f"Created window with resolution: {width}x{height}")
        else:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            # Let the window use system resolution in fullscreen
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def update_display(self, frame, wait_time: int) -> str:
        """Update the display and handle window events."""
        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(wait_time) & 0xFF
        if key == ord('q'):
            return 'q'
        elif key == ord('s'):
            return 's'
        elif key == ord('f'):  # Use 'f' key to toggle fullscreen
            self.toggle_fullscreen()
        return ''
    
    def cleanup(self) -> None:
        """Cleanup UI resources."""
        cv2.destroyAllWindows()
        if self.root and self.root.winfo_exists():  # Check if root window still exists
            self.root.destroy()
    
    def toggle_fullscreen(self):
        """Toggle fullscreen state for the video window."""
        if platform.machine().startswith('arm'):  # On Raspberry Pi
            # Toggle between fullscreen and normal
            self.fullscreen = not self.fullscreen
            
            # First set to normal to reset window state
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            cv2.waitKey(100)  # Wait for window state to update
            
            # Then set to desired state
            cv2.setWindowProperty(
                self.window_name,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL
            )
            
            # Force portrait mode
            width = int(self.settings['display_width'].get())
            height = int(self.settings['display_height'].get())
            if width > height:  # Ensure portrait orientation
                self.settings['display_width'].set(str(height))
                self.settings['display_height'].set(str(width))
            
            # If not fullscreen, set window size
            if not self.fullscreen:
                cv2.resizeWindow(self.window_name, width, height)
            return
            
        # Non-Raspberry Pi behavior
        self.fullscreen = not self.fullscreen
        cv2.setWindowProperty(
            self.window_name,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL
        )
        if not self.fullscreen:
            # When exiting fullscreen, maintain portrait orientation if needed
            width = int(self.settings['display_width'].get())
            height = int(self.settings['display_height'].get())
            cv2.resizeWindow(self.window_name, width, height)
