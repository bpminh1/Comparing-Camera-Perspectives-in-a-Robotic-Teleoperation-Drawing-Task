import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mujoco
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from src.experiments import DrawingExperiment
from src.config import ExperimentConfig

def main():
    '''Main function to set up and run the drawing experiment. 
    It loads the experiment configuration, initializes the MuJoCo model and data, sets up the MediaPipe hand landmarker, and starts the experiment.
    '''
    config = ExperimentConfig.from_yaml('config/experiment_config.yaml')

    # Path to the MuJoCo XML model
    spec = mujoco.MjSpec.from_file(config.mujoco_model)
    model = spec.compile()
    data = mujoco.MjData(model)

    # Path to the hand landmarker model
    model_path = config.mediapipe_model
    # Create an HandLandmarker object.
    base_options = python.BaseOptions(model_asset_path=model_path) # delegate=python.Delegate.CPU
    options = vision.HandLandmarkerOptions(base_options=base_options, running_mode=vision.RunningMode.VIDEO, num_hands=1)
    detector = vision.HandLandmarker.create_from_options(options)

    # Initialize and run the drawing experiment
    experiment = DrawingExperiment(config, spec, model, data, detector, config.participant_id)
    experiment.run()
    sys.exit(0)

if __name__ == "__main__":
    main()