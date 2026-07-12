import random as rnd
import os
from collections import deque
from src.config import ExperimentConfig

class TrialManager:
    '''This class manages the sequence of events in the experiment, including trials, slides, and questionnaires. 
    It builds a sequence of events based on the experiment configuration, and provides methods to retrieve the next event to execute. 
    The TrialManager allows for dynamic insertion of events (like the Block 3 trials after camera choice) and keeps track of the current trial number for data recording purposes.  
    '''

    def __init__(self, config: ExperimentConfig, runners, first_cam):
        self.config = config
        self.material_name = config.materials
        self.runners = runners
        self.cameras = [first_cam] + [cam for cam in self.config.camera_options if cam != first_cam]
        self.slides_dir = config.slides_dir
        self.slides = config.stationary_cam_slides if first_cam == 'stationary_cam' else config.dynamic_cam_slides

        self.sequence = deque()
        self._build_sequence()
        self.total_trials = sum(1 for event in self.sequence if event[0] == 'trial')
        self.current_trial = 0

    def _add_slides(self, slide_key_or_path):
        '''Adds slides to the sequence. The input can be a single slide key/path or a list of slide keys/paths.'''
        if isinstance(slide_key_or_path, list):
            slides =  [os.path.join(self.slides_dir, slide) for slide in slide_key_or_path]
        else:
            slides = [os.path.join(self.slides_dir, slide_key_or_path)]
        self.sequence.append(('slide', (slides, )))
        
    def _add_trial(self, shape, camera, save_data):
        ''''Adds a trial to the sequence with the specified shape, camera, and whether to save data.'''
        self.sequence.append(('trial', (shape, self.material_name[shape], camera, save_data)))

    def _add_slides_and_trial(self, repetitions, slide_key_or_path, shapes, camera, save_data):
        '''Adds a sequence of slides followed by trials for the specified shapes, repeated a certain number of times.'''
        self._add_slides(slide_key_or_path)
        shapes_randomized = shapes * repetitions
        if self.config.randomize_shapes:
            rnd.shuffle(shapes_randomized)
        for shape in shapes_randomized:
            self._add_trial(shape, camera, save_data)

    def _add_questionnaire(self, general, questions, options):
        '''Adds a questionnaire to the sequence with the specified questions and options.'''
        questionnaire_slide = os.path.join(self.slides_dir, self.config.questionnaire_slide)
        self.sequence.append(('questionnaire', (general, questions, options, questionnaire_slide)))
    
    def _build_sequence(self):
        '''Builds the sequence of events for the experiment based on the configuration.'''
        # Intro slides
        self._add_slides(self.config.intro_slides)

        # Tutorial
        self._add_slides_and_trial(self.config.tutorial_repetitions, self.slides['tutorial_slides'][0], self.config.tutorial_shape, self.cameras[0], False)
        self._add_slides_and_trial(self.config.tutorial_repetitions, self.slides['tutorial_slides'][1], self.config.tutorial_shape, self.cameras[1], False)

        # Block 1
        self._add_slides_and_trial(self.config.block1_repetitions, self.slides['block1_slide'], self.config.shapes, self.cameras[0], True)
        self._add_slides(self.config.end_block_slide)
        self._add_questionnaire(True, self.config.questionnaires['general'], self.cameras[0])

        # Block 2
        self._add_slides_and_trial(self.config.block2_repetitions, self.slides['block2_slide'], self.config.shapes, self.cameras[1], True)
        self._add_slides(self.config.end_block_slide)
        self._add_questionnaire(True, self.config.questionnaires['general'], self.cameras[1])
        
        # Preference questionnaire
        self._add_questionnaire(False, self.config.questionnaires['preference'], ['In General'] + self.config.shapes)
        
        # Camera choice
        self.sequence.append(('choice', (os.path.join(self.slides_dir, self.slides['choose_camera_slide']), )))
        
        # Block 3 placeholder - will be filled after camera choice
        self.sequence.append(('block3_placeholder', None))
        
        # Last slide
        self._add_slides(self.config.last_slide)

    def create_block3(self, chosen_cam):
        '''Creates the Block 3 trials based on the chosen camera and inserts them into the sequence after the camera choice event.'''
        block3_slide = self.config.block3_slide_stationary_cam if chosen_cam == 'stationary_cam' else self.config.block3_slide_dynamic_cam
        old_sequence = list(self.sequence)
        self.sequence = deque()

        for event in old_sequence:
            if event[0] == 'block3_placeholder':
                self._add_slides_and_trial(self.config.block3_repetitions, block3_slide, self.config.shapes, chosen_cam, True)
            else:
                self.sequence.append(event)

    def has_next(self):
        ''''Checks if there are more events in the sequence to execute.'''
        return len(self.sequence) > 0

    def get_next_trial(self):
        '''Retrieves the next event from the sequence and returns the corresponding runner and its arguments. 
        If the event is a trial, it also updates the current trial number for data recording purposes.
        '''
        if not self.has_next():
            return None, None
        
        event_type, event_args = self.sequence.popleft()
        
        if event_type == 'trial':
            shape, material, camera, save_data = event_args
            if save_data:
                self.current_trial += 1
            event_args = (shape, material, self.current_trial, camera, save_data)
        
        return self.runners[event_type], event_args