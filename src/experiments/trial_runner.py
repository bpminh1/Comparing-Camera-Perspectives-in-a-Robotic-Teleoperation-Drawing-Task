import cv2
import time
from src.core import SliderQuestionnaire, RadioButtonQuestionnaire
from .trial_state import TrialState, ChooseCamState, SlideState

class TrialRunner:
    '''This class is responsible for executing the trials, handling the main loop for each trial, processing camera input, and coordinating with the renderer and data recorder. 
    It manages the state of the current trial, including hand tracking, robot control, rendering, and data recording. 
    The TrialRunner also handles the execution of questionnaires and camera choice events, using the provided callbacks to control the flow of the experiment based on user input. 
    '''

    def __init__(self, data_recorder, hand_tracker, robot_controller, mujoco_renderer, experiment_callbacks):
        self.data_recorder = data_recorder
        self.hand_tracker = hand_tracker
        self.robot_controller = robot_controller
        self.mujoco_renderer = mujoco_renderer
        self.experiment_callbacks = experiment_callbacks
        self.state = None

    def run_trial(self, cap, global_exit_flag, shape_name, material_name, trial, camera, save_data):
        '''Runs a single trial event of the experiment.'''
        self.state = TrialState()
        self.state.global_exit_flag = global_exit_flag
        callback = self.experiment_callbacks.create_trial_callback(self.state, self.mujoco_renderer)
        self.mujoco_renderer.prepare_trial_conditions(material_name, camera, callback)

        start_time = time.perf_counter()
        # Show timer for practice trials, but not for data-collecting trials
        if not save_data:
            self.mujoco_renderer.set_text('01:00')

        while self._should_continue():
            if self._process_frame(cap):
                self.state.handle_drawing()
                self._render_scene()
                self.state.record_latency()
            
            # Update the display text (timer and status)
            self._show_text(start_time, not save_data)
        end_time = time.perf_counter()

        if save_data:
          self._save_data(camera, shape_name, trial, end_time - start_time)

    def run_questionnaire(self, cap, global_exit_flag, general, questions, options, slide):
        '''Runs a questionnaire event in the experiment.'''
        self.mujoco_renderer.set_image(slide)
        
        if general:
            questionnaire = SliderQuestionnaire(questions, options) # options = camera
        else:
            questionnaire = RadioButtonQuestionnaire(questions, options) # options = ['In General', shape names]

        responses = questionnaire.run()
        self.data_recorder.save_questionnaire_responses(responses, options)

        self.mujoco_renderer.clear_image()
    
    def run_choose_cam(self, cap, global_exit_flag, img_path):
        '''Runs the camera choice event in the experiment.'''
        self.state = ChooseCamState()
        self.state.global_exit_flag = global_exit_flag
        callback = self.experiment_callbacks.create_camera_choice_callback(self.state)

        self.mujoco_renderer.set_key_callback(callback)
        self.mujoco_renderer.set_image(img_path)
        
        while self._should_continue():
            self.mujoco_renderer.viewer.sync() # Just keep the viewer responsive while waiting for user input

        if self.state.go_next:
            self.mujoco_renderer.clear_image()

    def run_slide(self, cap, global_exit_flag, slide_paths):
        '''Runs a sequence of instruction slides in the experiment.'''
        self.state = SlideState()
        self.state.global_exit_flag = global_exit_flag
        callback = self.experiment_callbacks.create_slide_callback(self.state)
        self.mujoco_renderer.set_key_callback(callback)

        while not self.state.global_exit_flag['exit'] and not self.state.finish:
            if self.state.go_next:
                if slide_paths:
                    self.state.go_next = False
                    self.mujoco_renderer.set_image(slide_paths.pop(0))
                else:
                    self.state.finish = True

            self.mujoco_renderer.viewer.sync()

        self.mujoco_renderer.clear_image()

    def _should_continue(self):
        '''Determines whether the trial loop should continue running based on the state of the viewer, 
        whether the participant has indicated to proceed to the next trial, 
        and whether there is a global exit flag set.
        '''
        return (self.mujoco_renderer.is_viewer_running() and 
                not self.state.go_next and 
                not self.state.global_exit_flag['exit'])

    def _process_frame(self, cap):
        '''Captures a frame from the camera, processes it for hand tracking, and calculates the inverse kinematics for robot control.'''
        self.state.t_start = time.perf_counter()
        success, image = cap.read()
        if not success:
            return

        image = cv2.flip(image, 1)
        self.state.t_after_camera = time.perf_counter()
        self._detect_hand(image)
        return self._calculate_ik()
    
    def _detect_hand(self, image):
        '''Performs hand detection on the captured image and updates the state with the detected finger positions and timing information.'''
        timestamp_ms = int(time.perf_counter() * 1000)
        detection_result = self.hand_tracker.detect_hand(image, timestamp_ms)
        self.state.last_x, self.state.last_y = self.hand_tracker.get_finger_positions(detection_result, self.state.last_x, self.state.last_y)
        self.state.t_after_detection = time.perf_counter()
    
    def _calculate_ik(self):
        '''Calculates the inverse kinematics for the robot based on the detected hand positions.'''
        target_x, target_y = self.state.last_x, self.state.last_y
        z = 0.4
        if self.robot_controller.calculate_ik(target_x, target_y, z):
            self.state.t_after_ik = time.perf_counter()
            self.state.current_point = (target_x, target_y, z)
            return True
        return False

    def _render_scene(self):
        '''Renders the current scene in the mujoco viewer, including the robot and any drawn points.'''
        self.mujoco_renderer.render_scene(self.robot_controller.data, self.state.drawn_points)
        self.state.t_after_render = time.perf_counter()

    def _show_text(self, start_time, show_timer):
        '''Updates the text displayed in the mujoco viewer to show the remaining time for the trial and the current status (e.g., whether the participant is drawing).'''
        # Calculate timer info
        timer_text = None
        if show_timer:
            elapsed_time = time.perf_counter() - start_time
            remaining_time = 60 - elapsed_time
            
            if remaining_time <= 0:
                self.state.go_next = True
                return
            
            timer_text = f'00:{int(remaining_time):02d}'
        
        # Determine status text
        status_text = 'Drawing...' if self.state.is_drawing else None
        
        # Set display text
        if timer_text and status_text:
            self.mujoco_renderer.set_text(timer_text, status_text)
        elif timer_text:
            self.mujoco_renderer.set_text(timer_text)
        elif status_text:
            self.mujoco_renderer.set_text(status_text)
        else:
            self.mujoco_renderer.clear_text()   
            
    def _save_data(self, camera, shape_name, trial, duration):
        '''Saves the latency and trial data for the current trial.'''
        self.data_recorder.save_latency_stats(self.state.latency_data, trial)
        self.data_recorder.save_trial_data(camera, shape_name, self.state.drawn_points, self.state.moved_points, trial, duration)