from dataclasses import dataclass, field
from typing import List, Tuple, Dict

@dataclass
class TrialState:
    '''Maintains the state of a trial, including drawn points, moved points, drawing status, timing information, and latency data.'''

    drawn_points: List[List[Tuple[float, float, float]]] = field(default_factory=list)
    moved_points: List[List[Tuple[float, float, float]]] = field(default_factory=lambda: [[]])

    is_drawing: bool = False
    is_drawing_continued: bool = False
    last_x: float = 0.0
    last_y: float = 0.0
    current_point: Tuple[float, float, float] = None
    go_next: bool = False
    global_exit_flag: dict = field(default_factory=lambda: {'exit': False})

    t_start: float = 0.0
    t_after_camera: float = 0.0
    t_after_detection: float = 0.0
    t_after_ik: float = 0.0
    t_after_render: float = 0.0

    latency_data: Dict[str, List[float]] = field(default_factory=lambda: {
        'camera_capture': [],
        'camera_to_detection': [],
        'detection_to_ik': [],
        'ik_to_render': [],
        'end_to_end': []
    })

    def record_latency(self):
        '''Calculates and records the latency for each stage of the trial, as well as the end-to-end latency, and stores it in the latency_data dictionary.'''
        self.latency_data['camera_capture'].append(
            (self.t_after_camera - self.t_start) * 1000
        )
        self.latency_data['camera_to_detection'].append(
            (self.t_after_detection - self.t_after_camera) * 1000
        )
        self.latency_data['detection_to_ik'].append(
            (self.t_after_ik - self.t_after_detection) * 1000
        )
        self.latency_data['ik_to_render'].append(
            (self.t_after_render - self.t_after_ik) * 1000
        )
        self.latency_data['end_to_end'].append(
            (self.t_after_render - self.t_start) * 1000
        )

    def handle_drawing(self):
        '''Handles the drawing logic for the current trial, updating the drawn and moved points based on the current drawing state.'''
        if self.current_point is None:
            return
        
        if self.is_drawing:
            # If starting a new drawing
            if not self.drawn_points or not self.is_drawing_continued:
                self.drawn_points.append([self.current_point])
                self.moved_points.append([])
                self.is_drawing_continued = True
            # If continuing an existing drawing
            else:
                self.drawn_points[-1].append(self.current_point)
        # If not drawing
        else:
            self.moved_points[-1].append(self.current_point)

    def toggle_drawing(self):
        '''Toggles the drawing state for the current trial.'''
        self.is_drawing = not self.is_drawing
        if self.is_drawing:
            self.is_drawing_continued = False

@dataclass
class SlideState:
    '''Maintains the state of a slide sequence, including whether to proceed to the next slide, whether the sequence is finished, and a global exit flag.'''
    go_next: bool = True
    finish: bool = False
    global_exit_flag: dict = field(default_factory=lambda: {'exit': False})

@dataclass
class ChooseCamState:
    '''Maintains the state of a camera choice event, including the global exit flag and whether to proceed to the next step.'''
    global_exit_flag: dict = field(default_factory=lambda: {'exit': False})
    go_next: bool = False