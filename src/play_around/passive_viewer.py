import mujoco
import mediapy as media
import numpy as np
import mujoco.viewer
import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp
import os
import sys

# Add project root to path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.core import HandTracker, RobotController

xml = 'third_party/franka_emika_panda/scene.xml'
model = mujoco.MjModel.from_xml_path(xml)
data = mujoco.MjData(model)

# Initialize MediaPipe hand detector
model_path = 'third_party/mediapipe/hand_landmarker.task'
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

# Define workspace boundaries (same as drawing_experiment)
workspace_x_min, workspace_x_max = 0.06, 0.73
workspace_y_min, workspace_y_max = -0.43, 0.35
workspace_width = workspace_x_max - workspace_x_min
workspace_height = workspace_y_max - workspace_y_min

# Initialize hand tracker (for get_finger_positions only)
hand_tracker = HandTracker(
    detector,
    (workspace_x_min, workspace_x_max, workspace_y_min, workspace_y_max,
     workspace_width, workspace_height)
)

# Initialize robot controller
robot_controller = RobotController(
    data,
    (workspace_x_min, workspace_x_max, workspace_y_min, workspace_y_max)
)

# Open webcam
cap = cv2.VideoCapture(0)
cv2.waitKey(1000)  # Wait for camera to initialize

# Track last position
last_x, last_y = 0.35, 0.0
z = 0.4  # Fixed height for end-effector

# Launch interactive viewer
with mujoco.viewer.launch_passive(model, data) as viewer:
    # Reset simulation
    mujoco.mj_resetData(model, data)
    # Set viewer to use top camera
    viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
    viewer.cam.fixedcamid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "top")
    
    # Run simulation with hand tracking
    while viewer.is_running():
        # Read camera frame
        success, image = cap.read()
        if success:
            # Flip image for mirror effect
            image = cv2.flip(image, 1)
            
            # Detect hand WITHOUT showing OpenCV window
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            detection_result = detector.detect(mp_image)
            
            # Get finger position
            target_x, target_y = hand_tracker.get_finger_positions(
                detection_result, last_x, last_y
            )
            last_x, last_y = target_x, target_y
            
            # Calculate IK and update robot position
            if robot_controller.calculate_ik(target_x, target_y, z):
                # Step simulation
                mujoco.mj_step(model, data)
            
        # Sync viewer
        viewer.sync()

# Cleanup
cap.release()
cv2.destroyAllWindows()