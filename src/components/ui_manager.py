import cv2
import tkinter as tk
from tkinter import filedialog, ttk
import os
import json
from typing import Optional, Tuple, Dict

class UIManager:
    def __init__(self):
        # Initialize Tkinter
        self.root = tk.Tk()
        self.root.title("Video Display Settings")
        self.root.withdraw()  # Hide window initially
        
        # Settings file path
        self.settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        
        # Load saved settings or use defaults
        saved_settings = self.load_settings()
        
        # Settings variables with saved or default values
        self.settings = {
            'display_width': tk.StringVar(value=saved_settings.get('display_width', '1920')),
            'display_height': tk.StringVar(value=saved_settings.get('display_height', '1080')),
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
        
    def load_settings(self) -> Dict:
        """Load settings from JSON file"""
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
        """Save settings to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_current_settings(self) -> Dict:
        """Get current settings without showing UI"""
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
    
    def get_settings_with_ui(self) -> Dict:
        """Show UI and get settings"""
        self.root.deiconify()  # Show window
        return self.get_settings()
    
    def create_ui_elements(self):
        """Create all UI elements"""
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
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.started = False
    
    def browse_folder(self):
        """Open folder selection dialog"""
        initial_dir = self.settings['folder_path'].get() or os.path.expanduser('~')
        folder_path = filedialog.askdirectory(
            title='Select Video Folder',
            initialdir=initial_dir
        )
        if folder_path:
            self.settings['folder_path'].set(folder_path)
    
    def start(self):
        """Start button callback"""
        self.started = True
        self.root.withdraw()  # Hide window instead of quitting
        self.root.quit()
    
    def get_settings(self) -> Dict:
        """Run the UI and return the settings"""
        self.started = False
        self.root.mainloop()
        
        if not self.started:
            return None
            
        settings = self.get_current_settings()
        if settings:
            self.save_settings(settings)
        
        return settings
    
    def create_window(self) -> None:
        """Create and configure the OpenCV window"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
    
    def update_display(self, frame) -> str:
        """Update the display and handle window events"""
        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return 'q'
        elif key == ord('s'):
            return 's'
        return ''
    
    def cleanup(self) -> None:
        """Cleanup UI resources"""
        cv2.destroyAllWindows()
        if self.root:
            self.root.destroy() 