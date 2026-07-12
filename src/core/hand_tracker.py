import mediapipe as mp
import cv2
import numpy as np
from OneEuroFilter import OneEuroFilter

class HandTracker:
    '''This class handles hand tracking using MediaPipe. 
    It detects hand landmarks from the input camera feed and transforms them into mujoco workspace coordinates.
    The class also applies smoothing to the detected hand positions using a One Euro Filter.
    '''

    def __init__(self, detector, mj_workspace_bounds, world_workspace_bounds):
        self.detector = detector
        self.mj_workspace_x_min, self.mj_workspace_x_max, self.mj_workspace_y_min, self.mj_workspace_y_max, self.mj_workspace_width, self.mj_workspace_height = mj_workspace_bounds
        self.world_workspace_width, self.world_workspace_height = world_workspace_bounds

        self.camera_width = None
        self.camera_height = None
        self.H = None

        # Initialize One Euro Filters for x and y coordinates
        config = {
            'freq': 15,       # Hz
            'mincutoff': 1.0,  # Hz
            'beta': 0.01,       
            'dcutoff': 1.0    
            }
        self.f_x = OneEuroFilter(**config)
        self.f_y = OneEuroFilter(**config)

    def set_camera_calibration(self, camera_width, camera_height, H):
        '''Sets the camera calibration parameters. This should be called after calibrating the workspace.'''
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.H = H
     
    def detect_hand(self, image, timestamp_ms):
        '''Detects hand landmarks from the input image using MediaPipe.'''
        # Convert the image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        # Detect hand landmarks from the input image.
        detection_result = self.detector.detect_for_video(mp_image, timestamp_ms)

        return detection_result
    
    def get_finger_positions(self, detection_result, last_x, last_y):
        '''Transforms the detected hand landmarks into mujoco workspace coordinates.
        If the homography matrix (H) is not available, it maps the normalized landmark coordinates to the workspace coordinates using the defined workspace bounds.
        The method applies smoothing to the detected hand positions using a One Euro Filter.
        '''
        if len(detection_result.hand_landmarks) == 0:
            return last_x, last_y
        
        # Get the index finger tip position (landmark 8)
        hand_landmarks_list = detection_result.hand_landmarks[0]
        index_finger_tip = hand_landmarks_list[8]

        if self.H is None: 
            # Map the normalized landmark coordinates to the workspace coordinates
            target_x = self.mj_workspace_x_min + index_finger_tip.y * self.mj_workspace_width
            target_y = self.mj_workspace_y_min + index_finger_tip.x * self.mj_workspace_height

            # Apply smoothing
            smoothed_x = self.f_x(target_x)
            smoothed_y = self.f_y(target_y)
            return smoothed_x, smoothed_y

        # Convert MediaPipe normalized coords to camera pixel coords
        pixel_x = index_finger_tip.x * self.camera_width
        pixel_y = index_finger_tip.y * self.camera_height

        # Apply homography to map camera pixel coords to world coords
        point = np.array([pixel_x, pixel_y, 1.0])
        mapped = self.H @ point
        mapped /= mapped[2]

        x_world = mapped[0]
        y_world = mapped[1]

        # Normalize world coordinates to [0, 1]
        x_norm = x_world / self.world_workspace_width
        y_norm = y_world / self.world_workspace_height

        # Map to mujoco workspace coordinates
        x_mj = self.mj_workspace_x_min + (1 - y_norm) * self.mj_workspace_width
        y_mj = self.mj_workspace_y_min + x_norm * self.mj_workspace_height

        # Apply smoothing
        smoothed_x = self.f_x(x_mj)
        smoothed_y = self.f_y(y_mj)
        return smoothed_x, smoothed_y