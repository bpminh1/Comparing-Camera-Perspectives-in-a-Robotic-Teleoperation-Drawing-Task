class ExperimentCallbacks:
    '''This class defines the callback functions for handling user input during the experiment. 
    It provides methods to create specific callbacks for different stages of the experiment, such as trial execution, camera choice, and instruction slides. 
    The callbacks handle key events to control the flow of the experiment, allowing the participant to navigate through trials and make choices using the keyboard.
    '''

    def __init__(self, config, first_cam):
        self.config = config
        self.first_cam = first_cam
        self.other_cam = self._get_other_camera()
        self.chosen_cam = None

    def _get_other_camera(self):
        '''Determines the other camera option based on the first camera choice.'''
        cameras = [cam for cam in self.config.camera_options if cam != self.first_cam]
        return cameras[0] if cameras else None
    
    def create_trial_callback(self, state, renderer):
        '''Creates a callback function for handling key events during the trial execution.
        The callback allows the participant to toggle drawing mode with the left arrow key, proceed to the next trial with the right arrow key, and exit the experiment with the ESC key.
        '''
        def callback(keycode):
            if keycode == 266 or keycode == 263: # left arrow
                renderer.clear_image()
                state.toggle_drawing()
            elif keycode == 267 or keycode == 262: # right arrow
                state.go_next = True
            if keycode == 256:  # ESC key
                state.global_exit_flag['exit'] = True
        return callback

    def create_camera_choice_callback(self, state):
        '''Creates a callback function for handling key events during the camera choice stage.
        The callback allows the participant to choose between the first and other camera options using the left and right arrow keys, and exit the experiment with the ESC key.
        '''
        def callback(keycode):
            if keycode == 266 or keycode == 263: # left arrow
                self.chosen_cam = self.first_cam
                state.go_next = True
            elif keycode == 267 or keycode == 262: # right arrow
                self.chosen_cam = self.other_cam
                state.go_next = True
            elif keycode == 256:  # ESC key
                state.global_exit_flag['exit'] = True
        return callback
    
    def create_slide_callback(self, state):
        '''Creates a callback function for handling key events during the instruction slides.
        The callback allows the participant to proceed to the next slide with the right arrow key, and exit the experiment with the ESC key.
        '''
        def callback(keycode):
            if keycode == 267 or keycode == 262: # right arrow
                state.go_next = True
            elif keycode == 256: # ESC key
                state.global_exit_flag['exit'] = True
        return callback