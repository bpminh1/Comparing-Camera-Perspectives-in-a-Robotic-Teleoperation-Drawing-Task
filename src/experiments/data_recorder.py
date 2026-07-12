import os
import numpy as np
import pandas as pd
import json

class DataRecorder:
    '''This class handles recording and saving of experimental data. 
    It provides methods to save camera calibration data, latency statistics, trial data (including drawn and moved points), and questionnaire responses. 
    The data is saved in a structured format (JSON for trial data and CSV for questionnaire responses and latency statistics) in the specified output directory.
    '''

    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def to_serializable(obj):
        '''Helper method to convert non-serializable objects (like numpy arrays) into serializable formats (like lists).'''
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        return obj

    def save_camera_calibration(self, camera_positions):
        '''Saves the camera calibration data.'''
        calibration_folder = os.path.join(self.output_dir, 'calibration')
        os.makedirs(calibration_folder, exist_ok=True)
        calibration_file = os.path.join(calibration_folder, 'calibration.json')
        with open(calibration_file, 'w') as f:
            json.dump(camera_positions, f, indent=2, default=DataRecorder.to_serializable)
        print(f"Saved camera calibration to {calibration_file}")

    def save_latency_stats(self, latency_data, trial):
        '''Saves the latency statistics for a given trial.'''
        stats = self._calculate_latency_stats(latency_data)
        latency_output_dir = os.path.join(self.output_dir, 'latency')
        os.makedirs(latency_output_dir, exist_ok=True)
        stats.to_csv(os.path.join(latency_output_dir, f'latency_stats_trial_{trial}.csv'))
    
    def save_trial_data(self, camera, shape_name, drawn_points, moved_points, trial, duration):
        '''Saves the trial data, including drawn and moved points, for a given trial.'''
        data_to_save = {
            "metadata": {
                "camera": camera,
                "shape": shape_name,
                "duration": duration
            },
            "drawn": drawn_points,
            "moved": moved_points
        }
        
        filename = os.path.join(self.output_dir, f'trial_{trial}.json')
        
        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        print(f"Saved trajectory to {filename}")

    def save_questionnaire_responses(self, responses, options):
        '''Saves the questionnaire responses.'''
        questionnaire_path = os.path.join(self.output_dir, 'questionnaire')
        os.makedirs(questionnaire_path, exist_ok=True)

        df = pd.DataFrame(list(responses.items()), columns=['Question', 'Response'])
        
        if isinstance(options, str):
            name = f'{options}_questionnaire.csv'
        else:
            name = 'preference_questionnaire.csv'
            
        df.to_csv(os.path.join(questionnaire_path, name), index=False)
        print(f"Saved questionnaire responses to {os.path.join(questionnaire_path, name)}")

    @staticmethod
    def _calculate_latency_stats(latency_data):
        '''Calculates latency statistics for the given latency data.'''
        stats = {}
        for key, values in latency_data.items():
            if values:
                stats[key] = {
                    'Mean (ms)': np.mean(values),
                    'Median (ms)': np.median(values),
                    'Std (ms)': np.std(values),
                    'Min (ms)': np.min(values),
                    'Max (ms)': np.max(values),
                    '95th Percentile (ms)': np.percentile(values, 95)
                }
        return pd.DataFrame(stats).T