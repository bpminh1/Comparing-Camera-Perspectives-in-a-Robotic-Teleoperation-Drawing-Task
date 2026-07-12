import cv2
import os
from src.core import HandTracker, RobotController, MujocoRenderer, CameraCalibration
from .trial_manager import TrialManager
from .data_recorder import DataRecorder
from .trial_runner import TrialRunner
from .experiment_callbacks import ExperimentCallbacks

class DrawingExperiment:
    '''This class manages the overall flow of the drawing experiment. 
    It initializes the necessary components (hand tracker, robot controller, renderer, data recorder), 
    handles the main experiment loop, and coordinates the execution of trials and data recording. 
    The experiment involves detecting hand movements, controlling a robot arm in a MuJoCo simulation, and recording the data for analysis.
    '''

    def __init__(self, config, spec, model, data, detector, participant_id):
        # Initialize the experiment with the MuJoCo model, data, renderer, and MediaPipe hand detector
        self.config = config
        self.spec = spec
        self.model = model
        self.data = data

        self.output_dir = os.path.join(config.output_dir, participant_id)
        os.makedirs(self.output_dir, exist_ok=True)

        # Define workspace boundaries
        self.mj_workspace_x_min, self.mj_workspace_x_max = config.mj_workspace_x_min, config.mj_workspace_x_max
        self.mj_workspace_y_min, self.mj_workspace_y_max = config.mj_workspace_y_min, config.mj_workspace_y_max
        self.mj_workspace_width = self.mj_workspace_x_max - self.mj_workspace_x_min
        self.mj_workspace_height = self.mj_workspace_y_max - self.mj_workspace_y_min
        self.world_workspace_width, self.world_workspace_height = config.world_workspace_width, config.world_workspace_height

        self.hand_tracker = HandTracker(
            detector, 
            (self.mj_workspace_x_min, self.mj_workspace_x_max,
            self.mj_workspace_y_min, self.mj_workspace_y_max,
            self.mj_workspace_width, self.mj_workspace_height),
            (self.world_workspace_width, self.world_workspace_height)
        )

        self.robot_controller = RobotController(
            data, 
            (self.mj_workspace_x_min, self.mj_workspace_x_max,
            self.mj_workspace_y_min, self.mj_workspace_y_max)
        )

        self.camera_calibration = CameraCalibration()
        self.mujoco_renderer = MujocoRenderer(self.spec, self.model)
        self.recorder = DataRecorder(self.output_dir)
        self.trial_runner = TrialRunner(self.recorder, self.hand_tracker, self.robot_controller, self.mujoco_renderer, ExperimentCallbacks(config, config.first_camera))

    def run(self):
        '''Runs the main experiment loop.'''
        cap = cv2.VideoCapture(0)
        cv2.waitKey(1000)

        # Calibrate the workspace and save the calibration data
        camera_width, camera_height, H = self.camera_calibration.calibrate_workspace(cap)
        self.hand_tracker.set_camera_calibration(camera_width, camera_height, H)
        camera_positions = self.camera_calibration.find_camera_offset()
        self.recorder.save_camera_calibration(camera_positions)
    
        global_exit_flag = {'exit': False}

        self.mujoco_renderer.launch_viewer(self.data)
        
        # Initialize the TrialManager with the appropriate runners
        trial_manager = TrialManager(
            self.config, 
            runners={'trial': self.trial_runner.run_trial,
                     'questionnaire': self.trial_runner.run_questionnaire,
                     'choice': self.trial_runner.run_choose_cam,
                     'slide': self.trial_runner.run_slide},
            first_cam=self.config.first_camera)
        
        while trial_manager.has_next() and not global_exit_flag['exit']:
            # Get the next trial runner and execute it
            runner, args = trial_manager.get_next_trial()
            runner(cap, global_exit_flag, *args)
            
            if self.trial_runner.experiment_callbacks.chosen_cam is not None:
                trial_manager.create_block3(self.trial_runner.experiment_callbacks.chosen_cam)
                self.trial_runner.experiment_callbacks.chosen_cam = None
        
        self.mujoco_renderer.close()
        cap.release()
        cv2.destroyAllWindows()