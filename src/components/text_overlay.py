import cv2
import numpy as np
from typing import Tuple
import random
import math

class TextOverlay:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.4
        self.font_thickness = 1
        
        # Generate random bright colors for different elements
        self.text_color = self._generate_bright_color()
        self.line_color = self._generate_bright_color()
        self.grid_color = self._generate_bright_color()
        
        # Fixed measurements with scientific-sounding names
        self.measurements = [
            ('NEUTRINO OSCILLATION', {'min': 0.001, 'max': 9.999, 'unit': 'NO'}),
            ('GRAVITON FLUX', {'min': 20.0, 'max': 99.9, 'unit': 'GF'}),
            ('ENTROPY LEVEL', {'min': -273.15, 'max': 100.0, 'unit': 'EL'}),
            ('PHOTON DENSITY', {'min': 0.1, 'max': 1000.0, 'unit': 'PD'}),
            ('QUARK SPIN', {'min': 0.0, 'max': 1.0, 'unit': 'QS'}),
            ('HIGGS FIELD', {'min': 0.01, 'max': 10.0, 'unit': 'HF'}),
            ('QUANTUM ENTANGLEMENT', {'min': 0.0001, 'max': 1.0, 'unit': 'QE'}),
            ('TACHYON PULSE', {'min': 100.0, 'max': 999.9, 'unit': 'TP'}),
            ('DARK ENERGY FLUX', {'min': 0.01, 'max': 100.0, 'unit': 'DE'}),
            ('PLASMA RESONANCE', {'min': 1.0, 'max': 500.0, 'unit': 'PR'}),
            ('QUANTUM TUNNELING', {'min': 0.001, 'max': 0.999, 'unit': 'QT'}),
            ('ANTIMATTER DENSITY', {'min': 0.0, 'max': 1.0, 'unit': 'AD'})
        ]
        
        # Store static values and change rates for each object
        self.object_values = {}
        self.value_change_rates = {}

    def _generate_bright_color(self):
        """Generate a random bright color"""
        return tuple(np.random.randint(200, 256, 3).tolist())

    def render(self, display: np.ndarray, text: str, position: Tuple[int, int], 
               rotation: int = 0, display_width: int = None, display_height: int = None) -> None:
        """Render text overlay"""
        x, y = position
        
        # Generate a unique identifier for this position
        pos_id = f"{x}_{y}"
        
        # If this position doesn't have a measurement yet, assign one
        if pos_id not in self.object_values:
            name, params = random.choice(self.measurements)
            value = random.uniform(params['min'], params['max'])
            self.object_values[pos_id] = (name, value, params['unit'], params)
            # Set a random change rate (0.1% to 1% of range per frame)
            value_range = params['max'] - params['min']
            self.value_change_rates[pos_id] = random.uniform(0.001, 0.01) * value_range
        
        # Get the stored values and update them
        name, value, unit, params = self.object_values[pos_id]
        change_rate = self.value_change_rates[pos_id]
        
        # Update value with small oscillation
        new_value = value + change_rate * math.sin(cv2.getTickCount() / 500.0)
        
        # Keep within bounds
        new_value = max(params['min'], min(params['max'], new_value))
        self.object_values[pos_id] = (name, new_value, unit, params)
        
        # Draw measurements above container with reduced padding
        start_y = max(y - 25, 10)  # Reduced padding
        
        # Draw text
        text = f"{name}: {new_value:.3f} {unit}"
        cv2.putText(display, text, (x, start_y), 
                   self.font, self.font_scale, self.text_color, 
                   self.font_thickness, cv2.LINE_AA)
        
        # Draw single line under the text with minimal padding
        final_y = start_y + 8
        cv2.line(display,
                (x - 5, final_y + 2),
                (display.shape[1] - 10, final_y + 2),
                self.line_color, 1, cv2.LINE_AA)