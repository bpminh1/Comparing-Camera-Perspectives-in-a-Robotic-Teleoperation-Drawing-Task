import os
import json
import cv2
import mujoco
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.mujoco_renderer import MujocoRenderer

xml = os.path.join('third_party', 'franka_emika_panda', 'scene.xml')
spec = mujoco.MjSpec.from_file(xml)
model = None
data = None
renderer = None

def init_renderer():
    '''Initializes the Mujoco renderer for offscreen rendering. This is used to render the target shapes and the drawn trajectories without displaying a window.'''
    global model, data, renderer
    model = spec.compile()
    data = mujoco.MjData(model)
    if renderer:
        renderer.close()
    renderer = MujocoRenderer(spec, model, show_window=False)

def crop_canvas_region(img):
    '''Crops the region of the image that corresponds to the drawing canvas in the MuJoCo simulation.
    The crop region can be calculated using find_coordinate.py to find the pixel coordinates of the corners of the canvas in the rendered images.
    '''
    return img[458:1027, 996:1565]

def binarize_image(img):
    '''Converts the input image to a binary image where the drawn shape is represented by white pixels on a black background.'''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    return binary

def create_overlay(img_target, img_drawn):
    '''Creates an overlay image that combines the target shape and the drawn shape for visualization.'''
    overlay = np.zeros((img_target.shape[0], img_target.shape[1], 3), dtype=np.uint8)
    overlay[:, :, 2] = img_target  # Red channel = target
    overlay[:, :, 1] = img_drawn   # Green channel = drawn
    return overlay

def save_image(img, filepath):
    '''Saves the given image to the specified filepath, creating directories if necessary.'''
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    cv2.imwrite(filepath, img)

def save_all_target_shapes():
    '''Renders and saves the target shapes used in the experiment.'''
    global model, data, renderer
    init_renderer()

    save_path = os.path.join('data', 'target_shapes')
    os.makedirs(save_path, exist_ok=True)

    target_shapes_path = os.path.join('third_party', 'franka_emika_panda', 'assets', 'target_shapes')
    for shape_path in os.listdir(target_shapes_path):
        if shape_path.endswith('.png'):
            try:
                shape_name = os.path.splitext(shape_path)[0]
                
                # Save the full rendered image (for reference)
                renderer.set_material(f'{shape_name}_mat')
                img = renderer.render_offscreen(data, [])
                save_image(img, os.path.join(save_path, f'{shape_name}_full.png'))

                # Crop, binarize, and save the processed image for analysis
                img = crop_canvas_region(img)
                img = binarize_image(img)
                save_image(img, os.path.join(save_path, f'{shape_name}.png'))
                
                print(f"✓ Processed: {shape_name}")
            except Exception as e:
                print(f"✗ Error processing {shape_name}: {e}")
                continue

def save_one_trial(trial_path, participant_save_path, participant_trajectories_path, trials_info):
    '''Processes a single trial by rendering the target shape and the drawn trajectory, saving the images, and recording the trial information for analysis.'''
    trial = os.path.splitext(trial_path)[0]
    trial_save_path = os.path.join(participant_save_path, trial)
    os.makedirs(trial_save_path, exist_ok=False)

    with open(os.path.join(participant_trajectories_path, trial_path), 'r') as f:
        json_data = json.load(f)
        drawn = json_data['drawn']
        moved = json_data['moved']

        # Save target image
        shape = json_data['metadata']['shape']
        target_path = os.path.join('data', 'target_shapes', f'{shape}.png')
        target_img = cv2.imread(target_path, cv2.IMREAD_GRAYSCALE)
        save_image(target_img, os.path.join(trial_save_path, 'target.png'))

        # Save drawn image
        drawn_img = renderer.render_offscreen(data, drawn)
        drawn_img = crop_canvas_region(drawn_img)
        drawn_img = binarize_image(drawn_img)
        save_image(drawn_img, os.path.join(trial_save_path, 'drawn.png'))

        # Save the full rendered image with both target and drawn shapes for reference
        whole_img = renderer.render_offscreen(data, drawn, moved)
        save_image(whole_img, os.path.join(trial_save_path, 'whole.png'))

        # Create and save the overlay image for visualization
        overlay = create_overlay(target_img, drawn_img)
        save_image(overlay, os.path.join(trial_save_path, 'overlay.png'))

        trials_info.append({
            'trial': trial,
            'shape': shape
        })

def save_one_participant(participant, trajectories_path, save_path):
    '''Processes all trials for a single participant, saving the images and recording the trial information for analysis.'''
    participant_trajectories_path = os.path.join(trajectories_path, participant)
    participant_save_path = os.path.join(save_path, participant)
    os.makedirs(participant_save_path, exist_ok=False)

    trials_info = []
    init_renderer()

    for trial_path in os.listdir(participant_trajectories_path):
        if trial_path.endswith('.json'):
            try:
                save_one_trial(trial_path, participant_save_path, participant_trajectories_path, trials_info)
                print(f"✓ Processed: {participant} - {trial_path}")
            except Exception as e:
                print(f"✗ Error processing {participant} - {trial_path}: {e}")

    df = pd.DataFrame(trials_info)
    df.to_csv(os.path.join(participant_save_path, 'summary.csv'), index=False)

def save_all_participants(trajectories_path):
    '''Processes all participants, saving the images and recording the trial information for analysis.'''
    save_path = os.path.join('data', 'analysed')
    os.makedirs(save_path, exist_ok=True)

    for participant in os.listdir(trajectories_path):
        save_one_participant(participant, trajectories_path, save_path)
        print(f"✓ Processed: {participant}")