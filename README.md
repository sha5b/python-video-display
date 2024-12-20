# Python Video Display

A Python-based video player application designed to run on Raspberry Pi with autostart capabilities.

## Requirements

- Raspberry Pi (tested on Raspberry Pi 4)
- Python 3.x
- X Server running on Raspberry Pi
- Git (for cloning the repository)
- GStreamer (for video processing)

### Python Dependencies
- numpy (v1.24.3)
- opencv-python-headless (v4.8.1.78)
- gstreamer-python (v0.3.0)

## Installation

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly python3-gst-1.0
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/python-video-display.git
cd python-video-display
```

3. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Raspberry Pi
```

4. Install required dependencies:
```bash
pip install -r requirements.txt
```

## How It Works

The Python Video Display is a sophisticated video player designed for Raspberry Pi that:
- Loads videos from a specified directory
- Displays videos with hardware acceleration using GStreamer on Raspberry Pi
- Supports multiple video objects with dynamic scaling and positioning
- Automatically handles portrait/landscape orientation
- Maintains aspect ratio while filling the display
- Uses OpenCV for video processing with hardware acceleration optimizations

### Key Features
- Hardware-accelerated video playback
- Dynamic multi-video display
- Automatic aspect ratio handling
- Portrait mode support for Raspberry Pi
- Configurable video object scaling and positioning
- Real-time UI for settings adjustment
- Fullscreen support

## Usage

### Controls
- `F`: Toggle fullscreen mode
- `S`: Open settings UI to adjust parameters
- `Q`: Quit the application

### Settings UI
The application provides a graphical settings interface that can be accessed by:
1. Pressing `S` during video playback
2. Automatically on first run
3. When no videos are found in the configured folder

The settings UI allows you to configure:
- Display resolution (width/height)
- Number of simultaneous video objects (min/max)
- Video object scaling factors (min/max)
- Video folder location

Default values:
- Display: 1920x1080 (automatically detects on Raspberry Pi)
- Objects: Min 2, Max 10
- Scale: Min 0.3, Max 1.0

#### Raspberry Pi Portrait Mode
When running on Raspberry Pi, the application automatically:
- Detects system resolution
- Forces portrait orientation (480x1920 default)
- Rotates landscape videos for portrait display
- Maintains proper aspect ratio scaling

### Video Requirements
- Supported formats: .mp4, .avi, .mov
- Videos should be placed in the directory specified by `folder_path` in settings.json
- Videos can be any resolution - they will be automatically scaled while maintaining aspect ratio

## Configuration

The application uses a `settings.json` file located in the `src` directory for configuration. This file controls various aspects of the video player:

```json
{
    "display_width": 1920,        # Display resolution width
    "display_height": 1080,       # Display resolution height
    "min_objects": 1,            # Minimum number of video objects to display
    "max_objects": 6,            # Maximum number of video objects to display
    "min_scale": 0.08,          # Minimum scale factor for video objects
    "max_scale": 1.5,           # Maximum scale factor for video objects
    "folder_path": "/path/to/videos"  # Directory containing video files to display
}
```

Ensure this file is properly configured with your settings before running the application. The `folder_path` should be an absolute path to a directory containing the video files you want to display. On Raspberry Pi, make sure the path is accessible to the user running the service.

### Configuration Options

- `display_width`, `display_height`: Set your display resolution (e.g., 1920x1080)
- `min_objects`, `max_objects`: Control how many video objects appear simultaneously (1-6 recommended)
- `min_scale`, `max_scale`: Control the size range of video objects (0.08-1.5 by default)
- `folder_path`: Directory containing the video files to be displayed

### Performance Tips
- For optimal performance on Raspberry Pi, the application uses GStreamer for hardware-accelerated video decoding
- Videos are automatically scaled to match the display resolution while maintaining aspect ratio
- Multiple video objects are managed efficiently with dynamic memory handling
- Portrait mode is automatically handled on Raspberry Pi with proper rotation

## Manual Running

To run the video player manually:
```bash
cd src
python video_player.py
```

## Autostart Setup on Raspberry Pi

To configure the video player to start automatically on boot:

1. Create a systemd service file:
```bash
sudo nano /etc/systemd/system/videoplayer.service
```

2. Add the following content to the service file (adjust paths as needed):
```ini
[Unit]
Description=Python Video Player
After=network.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/your_username/.Xauthority
ExecStart=/home/your_username/python-video-display/venv/bin/python /home/your_username/python-video-display/src/video_player.py
WorkingDirectory=/home/your_username/python-video-display/src
StandardOutput=inherit
StandardError=inherit
Restart=always
User=your_username

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable videoplayer.service
sudo systemctl start videoplayer.service
```

4. Check service status:
```bash
sudo systemctl status videoplayer.service
```

## Troubleshooting

### Display Issues
If the video player doesn't start properly, check:
1. X Server is running (`echo $DISPLAY` should return `:0`)
2. Correct permissions on .Xauthority file
3. Service logs: `sudo journalctl -u videoplayer.service`

### Service Management
- Stop service: `sudo systemctl stop videoplayer.service`
- Restart service: `sudo systemctl restart videoplayer.service`
- View logs: `sudo journalctl -u videoplayer.service -f`

## Project Structure

```
python-video-display/
├── src/
│   ├── video_player.py         # Main application file
│   ├── settings.json           # Configuration file
│   └── components/             # Component modules
│       ├── background_elements.py
│       ├── container_transform.py
│       ├── text_overlay.py
│       └── ui_manager.py
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Notes

- Ensure your Raspberry Pi is configured to boot to desktop environment
- The DISPLAY and XAUTHORITY environment variables in the service file must match your system configuration
- Adjust file paths in the service file according to your username and installation directory
