import yaml
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ExperimentConfig:
    # Participant
    participant_id: str
    first_camera: str

    # Workspace
    mj_workspace_x_min: float
    mj_workspace_x_max: float
    mj_workspace_y_min: float
    mj_workspace_y_max: float
    world_workspace_width: float
    world_workspace_height: float

    # Trial structure
    tutorial_shape: List[str]
    shapes: List[str]
    materials: Dict[str, str]
    tutorial_repetitions: int
    block1_repetitions: int
    block2_repetitions: int
    block3_repetitions: int
    randomize_shapes: bool

    # Cameras
    camera_options: List[str]

    # Questionnaires:
    questionnaires: Dict[str, List[str]]

    # Paths
    mujoco_model: str
    mediapipe_model: str
    output_dir: str
    slides_dir: str
    intro_slides: List[str]
    end_block_slide: str
    questionnaire_slide: str
    block3_slide_stationary_cam: str
    block3_slide_dynamic_cam: str
    last_slide: str
    stationary_cam_slides: List[Dict[str, str | List[str]]]
    dynamic_cam_slides: List[Dict[str, str | List[str]]]

    @classmethod
    def from_yaml(cls, config_path: str) -> 'ExperimentConfig':
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return cls(
            participant_id=config['participant']['id'],
            first_camera=config['participant']['first_camera'],
            mj_workspace_x_min=config['mujoco_workspace']['x_min'],
            mj_workspace_x_max=config['mujoco_workspace']['x_max'],
            mj_workspace_y_min=config['mujoco_workspace']['y_min'],
            mj_workspace_y_max=config['mujoco_workspace']['y_max'],
            world_workspace_width=config['world_workspace']['width'],
            world_workspace_height=config['world_workspace']['height'],
            tutorial_shape=config['tutorial_shapes'],
            shapes=config['shapes'],
            materials=config['materials'],
            tutorial_repetitions=config['trial_structure']['tutorial_repetitions'],
            block1_repetitions=config['trial_structure']['block1_repetitions'],
            block2_repetitions=config['trial_structure']['block2_repetitions'],
            block3_repetitions=config['trial_structure']['block3_repetitions'],
            randomize_shapes=config['trial_structure']['randomize_shapes'],
            camera_options=config['cameras']['options'],
            questionnaires=config['questionnaires'],
            mujoco_model=config['paths']['mujoco_model'],
            mediapipe_model=config['paths']['mediapipe_model'],
            output_dir=config['paths']['output_dir'],
            slides_dir=config['paths']['slides_dir'],
            intro_slides=config['slides']['intro_slides'],
            end_block_slide=config['slides']['end_block_slide'],
            questionnaire_slide=config['slides']['questionnaire_slide'],
            block3_slide_stationary_cam=config['slides']['block3_slide_stationary_cam'],
            block3_slide_dynamic_cam=config['slides']['block3_slide_dynamic_cam'],
            last_slide=config['slides']['last_slide'],
            stationary_cam_slides=config['slides']['stationary_cam_slides'],
            dynamic_cam_slides=config['slides']['dynamic_cam_slides']
        )
